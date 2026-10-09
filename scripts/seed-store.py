"""
Creates the store data the Spa Time theme expects (idempotent: existing items are kept).

  metaobject definitions  uitvoering, kerncijfer, specificatie (+ entries)
  product metafields      custom.persons, badge, subtitle, tagline, key_specs, specs,
                          top_view, width_cm, length_cm, why_heading, highlights
  products                Ibiza, Bali, Marbella — Kuipkleur × Uitvoering (6 variants)
  collection              Jacuzzi's
  pages                   Over ons, Uitvoeringen, Waarom Spa Time (+ Contact template)
  menus                   main-menu, footer-collectie, footer-spatime, footer

Run (after `shopify store auth` with product/metaobject/page/navigation scopes):
  python3 scripts/seed-store.py
"""
import json
import subprocess
import sys
import os
import tempfile


sys.path.insert(0, os.path.dirname(__file__))
from content import MODELS, TIERS  # noqa: E402  (shared with sync-content.py)

STORE = 'spa-time-swqdbe9x.myshopify.com'


def gql(query, variables=None):
    with tempfile.NamedTemporaryFile('w', suffix='.graphql', delete=False) as q, \
            tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as v:
        q.write(query)
        json.dump(variables or {}, v)
    out = subprocess.run(
        ['shopify', 'store', 'execute', '--store', STORE, '--json', '--allow-mutations',
         '--query-file', q.name, '--variable-file', v.name],
        capture_output=True, text=True)
    start = out.stdout.find('{')
    if out.returncode or start < 0:
        sys.exit('GraphQL call failed:\n' + out.stdout + out.stderr)
    data = json.loads(out.stdout[start:])
    data = data.get('data', data)
    # Surface userErrors from any mutation payload.
    for payload in data.values():
        if isinstance(payload, dict) and payload.get('userErrors'):
            sys.exit('userErrors: ' + json.dumps(payload['userErrors'], ensure_ascii=False))
    return data


def log(msg):
    print('•', msg, flush=True)


# ---------------------------------------------------------------- metaobjects
def field(key, name, type_, **extra):
    return {'key': key, 'name': name, 'type': type_, **extra}


DEFINITIONS = {
    'uitvoering': ('Uitvoering', 'name', [
        field('name', 'Naam', 'single_line_text_field', required=True),
        field('subtitle', 'Ondertitel', 'single_line_text_field'),
        field('icon', 'Icoon', 'single_line_text_field', description='diamond, steam, star, …'),
        field('short_description', 'Korte omschrijving', 'multi_line_text_field'),
        field('description', 'Omschrijving', 'multi_line_text_field'),
        field('features', 'Kenmerken', 'list.single_line_text_field'),
        field('ideal_for', 'Ideaal voor', 'multi_line_text_field'),
        field('ideal_icon', 'Icoon "ideaal voor"', 'single_line_text_field'),
        field('image', 'Afbeelding', 'file_reference'),
        field('featured', 'Meest gekozen', 'boolean'),
    ]),
    'kerncijfer': ('Kerncijfer', 'label', [
        field('icon', 'Icoon', 'single_line_text_field'),
        field('value', 'Waarde', 'single_line_text_field', required=True),
        field('label', 'Label', 'single_line_text_field', required=True),
    ]),
    'specificatie': ('Specificatie', 'label', [
        field('label', 'Label', 'single_line_text_field', required=True),
        field('value', 'Waarde', 'single_line_text_field', required=True),
    ]),
}

existing = {d['type']: d['id'] for d in gql('{ metaobjectDefinitions(first: 50) { nodes { id type } } }')['metaobjectDefinitions']['nodes']}
definition_ids = {}
for type_, (name, display_key, fields) in DEFINITIONS.items():
    if type_ in existing:
        definition_ids[type_] = existing[type_]
        continue
    res = gql('''mutation($d: MetaobjectDefinitionCreateInput!) {
        metaobjectDefinitionCreate(definition: $d) { metaobjectDefinition { id } userErrors { field message } } }''',
              {'d': {'type': type_, 'name': name, 'displayNameKey': display_key, 'fieldDefinitions': fields,
                     'access': {'storefront': 'PUBLIC_READ'}}})
    definition_ids[type_] = res['metaobjectDefinitionCreate']['metaobjectDefinition']['id']
    log(f'metaobject definition {type_}')


def upsert_metaobject(type_, handle, fields):
    values = [{'key': k, 'value': v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)} for k, v in fields.items()]
    res = gql('''mutation($h: MetaobjectHandleInput!, $m: MetaobjectUpsertInput!) {
        metaobjectUpsert(handle: $h, metaobject: $m) { metaobject { id } userErrors { field message } } }''',
              {'h': {'type': type_, 'handle': handle}, 'm': {'fields': values}})
    return res['metaobjectUpsert']['metaobject']['id']


for handle, fields in TIERS:
    upsert_metaobject('uitvoering', handle, fields)
log('uitvoeringen Comfort, Premium, Signature')

# ---------------------------------------------------------------- product metafield definitions
MF = [
    ('persons', 'Personen', 'number_integer', None),
    ('badge', 'Label boven titel', 'single_line_text_field', None),
    ('subtitle', 'Ondertitel', 'single_line_text_field', None),
    ('tagline', 'Tagline (collectie)', 'single_line_text_field', None),
    ('key_specs', 'Kerncijfers', 'list.metaobject_reference', 'kerncijfer'),
    ('specs', 'Specificaties', 'list.metaobject_reference', 'specificatie'),
    ('top_view', 'Bovenaanzicht', 'file_reference', None),
    ('width_cm', 'Breedte (cm)', 'number_integer', None),
    ('length_cm', 'Lengte (cm)', 'number_integer', None),
    ('why_heading', 'Waarom-kop', 'multi_line_text_field', None),
    ('why_text', 'Waarom-tekst', 'multi_line_text_field', None),
    ('highlights', 'Waarom-punten', 'list.single_line_text_field', None),
]
have = {n['key'] for n in gql('{ metafieldDefinitions(first: 100, ownerType: PRODUCT, namespace: "custom") { nodes { key } } }')['metafieldDefinitions']['nodes']}
for key, name, type_, ref in MF:
    if key in have:
        continue
    d = {'name': name, 'namespace': 'custom', 'key': key, 'type': type_, 'ownerType': 'PRODUCT',
         'access': {'storefront': 'PUBLIC_READ'}}
    if ref:
        d['validations'] = [{'name': 'metaobject_definition_id', 'value': definition_ids[ref]}]
    gql('''mutation($d: MetafieldDefinitionInput!) {
        metafieldDefinitionCreate(definition: $d) { createdDefinition { id } userErrors { field message } } }''', {'d': d})
    log(f'metafield custom.{key}')

# ---------------------------------------------------------------- products
COLORS = [('White', 0), ('Marble White', 250)]

publications = gql('{ publications(first: 20) { nodes { id name } } }')['publications']['nodes']
online_store = next(p['id'] for p in publications if p['name'] == 'Online Store')

product_ids = []
for m in MODELS:
    found = gql('query($q: String!) { products(first: 1, query: $q) { nodes { id } } }', {'q': 'handle:' + m['handle']})['products']['nodes']
    if found:
        product_ids.append(found[0]['id'])
        continue
    key_specs = [upsert_metaobject('kerncijfer', f"{m['handle']}-{i + 1}", {'icon': ic, 'value': v, 'label': lb})
                 for i, (ic, v, lb) in enumerate(m['key_specs'])]
    specs = [upsert_metaobject('specificatie', f"{m['handle']}-{i + 1}", {'label': lb, 'value': v})
             for i, (lb, v) in enumerate(m['specs'])]
    metafields = [
        {'namespace': 'custom', 'key': 'persons', 'type': 'number_integer', 'value': str(m['persons'])},
        {'namespace': 'custom', 'key': 'badge', 'type': 'single_line_text_field', 'value': m['title'].upper()},
        {'namespace': 'custom', 'key': 'subtitle', 'type': 'single_line_text_field', 'value': m['subtitle']},
        {'namespace': 'custom', 'key': 'tagline', 'type': 'single_line_text_field', 'value': m['tagline']},
        {'namespace': 'custom', 'key': 'why_heading', 'type': 'multi_line_text_field', 'value': m['why_heading']},
        {'namespace': 'custom', 'key': 'why_text', 'type': 'multi_line_text_field', 'value': m['why_text']},
        {'namespace': 'custom', 'key': 'highlights', 'type': 'list.single_line_text_field', 'value': json.dumps(m['highlights'], ensure_ascii=False)},
        {'namespace': 'custom', 'key': 'key_specs', 'type': 'list.metaobject_reference', 'value': json.dumps(key_specs)},
    ]
    if specs:
        metafields.append({'namespace': 'custom', 'key': 'specs', 'type': 'list.metaobject_reference', 'value': json.dumps(specs)})
    if m['size']:
        metafields += [{'namespace': 'custom', 'key': 'length_cm', 'type': 'number_integer', 'value': str(m['size'][0])},
                       {'namespace': 'custom', 'key': 'width_cm', 'type': 'number_integer', 'value': str(m['size'][1])}]
    res = gql('''mutation($p: ProductCreateInput!) { productCreate(product: $p) { product { id } userErrors { field message } } }''',
              {'p': {'title': m['title'], 'handle': m['handle'], 'status': 'ACTIVE', 'vendor': 'Spa Time',
                     'productType': 'Jacuzzi', 'descriptionHtml': m['description'], 'metafields': metafields,
                     'productOptions': [{'name': 'Kuipkleur', 'values': [{'name': c} for c, _ in COLORS]},
                                        {'name': 'Uitvoering', 'values': [{'name': t} for t in m['prices']]}]}})
    pid = res['productCreate']['product']['id']
    variants = [{'price': str(price + extra), 'optionValues': [{'optionName': 'Kuipkleur', 'name': color},
                                                                {'optionName': 'Uitvoering', 'name': tier}],
                 'inventoryPolicy': 'CONTINUE', 'inventoryItem': {'tracked': False, 'requiresShipping': True}}
                for color, extra in COLORS for tier, price in m['prices'].items()]
    gql('''mutation($id: ID!, $v: [ProductVariantsBulkInput!]!) {
        productVariantsBulkCreate(productId: $id, variants: $v, strategy: REMOVE_STANDALONE_VARIANT) {
          productVariants { id } userErrors { field message } } }''', {'id': pid, 'v': variants})
    gql('''mutation($id: ID!, $i: [PublicationInput!]!) { publishablePublish(id: $id, input: $i) { userErrors { field message } } }''',
        {'id': pid, 'i': [{'publicationId': online_store}]})
    product_ids.append(pid)
    log(f"product {m['title']} (6 varianten)")

# ---------------------------------------------------------------- collection
found = gql('{ collections(first: 1, query: "handle:jacuzzis") { nodes { id } } }')['collections']['nodes']
if found:
    collection_id = found[0]['id']
else:
    res = gql('''mutation($c: CollectionInput!) { collectionCreate(input: $c) { collection { id } userErrors { field message } } }''',
              {'c': {'title': "Jacuzzi's", 'handle': 'jacuzzis', 'sortOrder': 'MANUAL', 'products': product_ids,
                     'descriptionHtml': '<p>Drie modellen, elk in drie uitvoeringen. Ontworpen voor jarenlang genieten.</p>'}})
    collection_id = res['collectionCreate']['collection']['id']
    gql('''mutation($id: ID!, $i: [PublicationInput!]!) { publishablePublish(id: $id, input: $i) { userErrors { field message } } }''',
        {'id': collection_id, 'i': [{'publicationId': online_store}]})
    log("collectie Jacuzzi's")

# ---------------------------------------------------------------- pages
PAGES = [('Over ons', 'over-ons', 'over'), ('Uitvoeringen', 'uitvoeringen', 'uitvoeringen'),
         ('Waarom Spa Time', 'waarom-spa-time', 'waarom'), ('Contact', 'contact', 'contact')]
page_ids = {}
for title, handle, suffix in PAGES:
    found = gql('query($q: String!) { pages(first: 1, query: $q) { nodes { id templateSuffix } } }', {'q': 'handle:' + handle})['pages']['nodes']
    if found:
        page_ids[handle] = found[0]['id']
        if found[0]['templateSuffix'] != suffix:
            gql('''mutation($id: ID!, $p: PageUpdateInput!) { pageUpdate(id: $id, page: $p) { page { id } userErrors { field message } } }''',
                {'id': found[0]['id'], 'p': {'templateSuffix': suffix}})
        continue
    res = gql('''mutation($p: PageCreateInput!) { pageCreate(page: $p) { page { id } userErrors { field message } } }''',
              {'p': {'title': title, 'handle': handle, 'templateSuffix': suffix, 'isPublished': True}})
    page_ids[handle] = res['pageCreate']['page']['id']
    log(f'pagina {title}')

# ---------------------------------------------------------------- menus
by_handle = dict(zip([m['handle'] for m in MODELS], product_ids))


def item(title, type_, resource=None, url=None, items=None):
    out = {'title': title, 'type': type_}
    if resource:
        out['resourceId'] = resource
    if url:
        out['url'] = url
    if items:
        out['items'] = items
    return out


models = [item(m['title'], 'PRODUCT', by_handle[m['handle']]) for m in MODELS]
MENUS = {
    'main-menu': ('Main menu', [
        item("Jacuzzi's", 'COLLECTION', collection_id, items=models + [item('Uitvoeringen vergelijken', 'PAGE', page_ids['uitvoeringen'])]),
        item('Collectie', 'COLLECTION', collection_id),
        item('Waarom Spa Time', 'PAGE', page_ids['waarom-spa-time']),
        item('Over ons', 'PAGE', page_ids['over-ons']),
        item('Showroom', 'HTTP', url='/pages/contact#showroom'),
        item('Contact', 'PAGE', page_ids['contact']),
    ]),
    'footer-collectie': ('Footer collectie', models + [item('Uitvoeringen', 'PAGE', page_ids['uitvoeringen'])]),
    'footer-spatime': ('Footer Spa Time', [
        item('Waarom Spa Time', 'PAGE', page_ids['waarom-spa-time']),
        item('Over ons', 'PAGE', page_ids['over-ons']),
        item('Contact', 'PAGE', page_ids['contact']),
    ]),
    'footer': ('Footer menu', [
        item('Algemene voorwaarden', 'HTTP', url='/policies/terms-of-service'),
        item('Privacy', 'HTTP', url='/policies/privacy-policy'),
    ]),
}
menus = {m['handle']: m['id'] for m in gql('{ menus(first: 50) { nodes { id handle } } }')['menus']['nodes']}
for handle, (title, items) in MENUS.items():
    if handle in menus:
        gql('''mutation($id: ID!, $t: String!, $h: String!, $i: [MenuItemUpdateInput!]!) {
            menuUpdate(id: $id, title: $t, handle: $h, items: $i) { menu { id } userErrors { field message } } }''',
            {'id': menus[handle], 't': title, 'h': handle, 'i': items})
    else:
        gql('''mutation($t: String!, $h: String!, $i: [MenuItemCreateInput!]!) {
            menuCreate(title: $t, handle: $h, items: $i) { menu { id } userErrors { field message } } }''',
            {'t': title, 'h': handle, 'i': items})
    log(f'menu {handle}')

print('Klaar.')
