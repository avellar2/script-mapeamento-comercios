import yaml
with open(r'C:\Users\Vanderson\AppData\Local\hermes\config.yaml') as f:
    c = yaml.safe_load(f)
print('model:', c.get('model'))
print('providers keys:', list(c.get('providers', {}).keys()))

# Also check the minimax provider config
if 'providers' in c:
    for k in c['providers']:
        if 'minimax' in k.lower() or 'ollama' in k.lower():
            print(f'Provider {k}:', c['providers'][k])