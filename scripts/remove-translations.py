"""
Removes translations for one locale from all translatable store content.

Needed once (Oct 2026): Dutch was added while English was still the primary
language, so Shopify auto-"translated" the (already Dutch) content into Dutch
("Showroom" → "Toonzaal", "Signature" → "Handtekening"). With Dutch as primary
those translations only get in the way.

Usage:  python3 scripts/remove-translations.py nl            # dry run: list
        python3 scripts/remove-translations.py nl --apply    # remove
"""
import json
import subprocess
import sys
import tempfile

STORE = 'spa-time-swqdbe9x.myshopify.com'
LOCALE = sys.argv[1] if len(sys.argv) > 1 else 'nl'
APPLY = '--apply' in sys.argv

# Only content we wrote in Dutch. Shopify/Horizon's own English content (404, cart, password,
# theme strings, filters, default policies) keeps its Dutch translation.
TYPES = ['COLLECTION', 'LINK', 'MENU', 'METAFIELD', 'METAOBJECT', 'PAGE', 'PRODUCT', 'PRODUCT_OPTION',
         'PRODUCT_OPTION_VALUE', 'ONLINE_STORE_THEME_JSON_TEMPLATE', 'ONLINE_STORE_THEME_SECTION_GROUP']
OWN_TEMPLATES = ('index?', 'collection?', 'product?', 'page?', 'page.contact?', 'page.over?', 'page.uitvoeringen?',
                 'page.waarom?', 'header-group?', 'footer-group?')


def gql(query, variables=None, allow_errors=False):
    with tempfile.NamedTemporaryFile('w', suffix='.graphql', delete=False) as q, \
            tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as v:
        q.write(query)
        json.dump(variables or {}, v)
    out = subprocess.run(['shopify', 'store', 'execute', '--store', STORE, '--json', '--allow-mutations',
                          '--query-file', q.name, '--variable-file', v.name], capture_output=True, text=True)
    start = out.stdout.find('{')
    if start < 0:
        if allow_errors:
            return None
        sys.exit(out.stdout + out.stderr)
    data = json.loads(out.stdout[start:])
    return data.get('data', data)


total = 0
for type_ in TYPES:
    cursor = None
    while True:
        data = gql('''query($t: TranslatableResourceType!, $after: String, $l: String!) {
            translatableResources(first: 100, resourceType: $t, after: $after) {
              nodes { resourceId translations(locale: $l) { key value } }
              pageInfo { hasNextPage endCursor } } }''', {'t': type_, 'after': cursor, 'l': LOCALE}, allow_errors=True)
        if not data or 'translatableResources' not in data:
            break
        res = data['translatableResources']
        for node in res['nodes']:
            keys = [t['key'] for t in node['translations']]
            if not keys:
                continue
            if type_.startswith('ONLINE_STORE_THEME') and not node['resourceId'].split('/')[-1].startswith(OWN_TEMPLATES):
                continue
            total += len(keys)
            sample = ', '.join(f"{t['key']}={t['value'][:30]!r}" for t in node['translations'][:2])
            print(f"{type_:<34} {node['resourceId'].split('/')[-1]:<20} {len(keys):>3}  {sample}")
            if APPLY:
                gql('''mutation($id: ID!, $k: [String!]!, $l: [String!]!) {
                    translationsRemove(resourceId: $id, translationKeys: $k, locales: $l) { userErrors { field message } } }''',
                    {'id': node['resourceId'], 'k': keys, 'l': [LOCALE]})
        if not res['pageInfo']['hasNextPage']:
            break
        cursor = res['pageInfo']['endCursor']

print(('Verwijderd' if APPLY else 'Gevonden') + f': {total} vertaalde velden ({LOCALE}).')
