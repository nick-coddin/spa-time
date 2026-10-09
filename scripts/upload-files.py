"""
Uploads local images to Shopify Files (Content › Files).
Usage: python3 scripts/upload-files.py path/to/file.png [...]
Prints the shopify://shop_images/<name> reference for theme settings.
"""
import json
import mimetypes
import os
import subprocess
import sys
import tempfile
import time

STORE = 'spa-time-swqdbe9x.myshopify.com'


def gql(query, variables=None):
    with tempfile.NamedTemporaryFile('w', suffix='.graphql', delete=False) as q, \
            tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as v:
        q.write(query)
        json.dump(variables or {}, v)
    out = subprocess.run(['shopify', 'store', 'execute', '--store', STORE, '--json', '--allow-mutations',
                          '--query-file', q.name, '--variable-file', v.name], capture_output=True, text=True)
    data = json.loads(out.stdout[out.stdout.find('{'):])
    data = data.get('data', data)
    for payload in data.values():
        if isinstance(payload, dict) and payload.get('userErrors'):
            sys.exit('userErrors: ' + json.dumps(payload['userErrors'], ensure_ascii=False))
    return data


for path in sys.argv[1:]:
    name = os.path.basename(path)
    mime = mimetypes.guess_type(name)[0] or 'image/png'
    target = gql('''mutation($i: [StagedUploadInput!]!) { stagedUploadsCreate(input: $i) {
        stagedTargets { url resourceUrl parameters { name value } } userErrors { field message } } }''',
                 {'i': [{'resource': 'IMAGE', 'filename': name, 'mimeType': mime, 'httpMethod': 'POST'}]})['stagedUploadsCreate']['stagedTargets'][0]
    form = []
    for p in target['parameters']:
        form += ['-F', f"{p['name']}={p['value']}"]
    subprocess.run(['curl', '-s', '-f', '-o', '/dev/null', *form, '-F', f'file=@{path}', target['url']], check=True)
    file = gql('''mutation($f: [FileCreateInput!]!) { fileCreate(files: $f) { files { id fileStatus } userErrors { field message } } }''',
               {'f': [{'originalSource': target['resourceUrl'], 'contentType': 'IMAGE', 'alt': 'Spa Time', 'filename': name}]})['fileCreate']['files'][0]
    for _ in range(20):
        node = gql('query($id: ID!) { node(id: $id) { ... on MediaImage { fileStatus image { url } } } }', {'id': file['id']})['node']
        if node['fileStatus'] == 'READY':
            break
        time.sleep(2)
    url = node['image']['url'] if node.get('image') else ''
    print(f"{name}: {node['fileStatus']}  shopify://shop_images/{url.split('/')[-1].split('?')[0] or name}")
