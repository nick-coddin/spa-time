"""
Pushes scripts/content.py to the store: overwrites the tier metaobjects and the
product metafields (specs, key figures, "Waarom"-texts, dimensions) of existing models.

Run: python3 scripts/sync-content.py
"""
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(__file__))
from content import MODELS, TIERS  # noqa: E402

STORE = 'spa-time-swqdbe9x.myshopify.com'


def gql(query, variables=None):
    with tempfile.NamedTemporaryFile('w', suffix='.graphql', delete=False) as q, \
            tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as v:
        q.write(query)
        json.dump(variables or {}, v)
    out = subprocess.run(['shopify', 'store', 'execute', '--store', STORE, '--json', '--allow-mutations',
                          '--query-file', q.name, '--variable-file', v.name], capture_output=True, text=True)
    start = out.stdout.find('{')
    if out.returncode or start < 0:
        sys.exit('GraphQL call failed:\n' + out.stdout + out.stderr)
    data = json.loads(out.stdout[start:])
    data = data.get('data', data)
    for payload in data.values():
        if isinstance(payload, dict) and payload.get('userErrors'):
            sys.exit('userErrors: ' + json.dumps(payload['userErrors'], ensure_ascii=False))
    return data


def upsert(type_, handle, fields):
    values = [{'key': k, 'value': v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)} for k, v in fields.items()]
    return gql('''mutation($h: MetaobjectHandleInput!, $m: MetaobjectUpsertInput!) {
        metaobjectUpsert(handle: $h, metaobject: $m) { metaobject { id } userErrors { field message } } }''',
               {'h': {'type': type_, 'handle': handle}, 'm': {'fields': values}})['metaobjectUpsert']['metaobject']['id']


def prune(type_, prefix, keep):
    """Delete entries like `bali-7` that are no longer used."""
    nodes = gql('query($t: String!) { metaobjects(type: $t, first: 250) { nodes { id handle } } }', {'t': type_})['metaobjects']['nodes']
    for n in nodes:
        if n['handle'].startswith(prefix + '-') and n['id'] not in keep:
            gql('mutation($id: ID!) { metaobjectDelete(id: $id) { deletedId userErrors { field message } } }', {'id': n['id']})


for handle, fields in TIERS:
    upsert('uitvoering', handle, fields)
print('• uitvoeringen bijgewerkt')

for m in MODELS:
    found = gql('query($q: String!) { products(first: 1, query: $q) { nodes { id } } }', {'q': 'handle:' + m['handle']})['products']['nodes']
    if not found:
        print(f"• {m['title']} bestaat niet, overgeslagen (eerst seed-store.py draaien)")
        continue
    pid = found[0]['id']
    key_specs = [upsert('kerncijfer', f"{m['handle']}-{i + 1}", {'icon': ic, 'value': v, 'label': lb}) for i, (ic, v, lb) in enumerate(m['key_specs'])]
    specs = [upsert('specificatie', f"{m['handle']}-{i + 1}", {'label': lb, 'value': v}) for i, (lb, v) in enumerate(m['specs'])]
    prune('kerncijfer', m['handle'], set(key_specs))
    prune('specificatie', m['handle'], set(specs))
    mf = lambda key, type_, value: {'ownerId': pid, 'namespace': 'custom', 'key': key, 'type': type_, 'value': value}
    gql('''mutation($m: [MetafieldsSetInput!]!) { metafieldsSet(metafields: $m) { metafields { id } userErrors { field message } } }''', {'m': [
        mf('persons', 'number_integer', str(m['persons'])),
        mf('subtitle', 'single_line_text_field', m['subtitle']),
        mf('tagline', 'single_line_text_field', m['tagline']),
        mf('why_heading', 'multi_line_text_field', m['why_heading']),
        mf('why_text', 'multi_line_text_field', m['why_text']),
        mf('highlights', 'list.single_line_text_field', json.dumps(m['highlights'], ensure_ascii=False)),
        mf('key_specs', 'list.metaobject_reference', json.dumps(key_specs)),
        mf('specs', 'list.metaobject_reference', json.dumps(specs)),
        mf('length_cm', 'number_integer', str(m['size'][0])),
        mf('width_cm', 'number_integer', str(m['size'][1])),
    ]})
    print(f"• {m['title']}: {len(specs)} specificaties, {len(key_specs)} kerncijfers")

print('Klaar.')
