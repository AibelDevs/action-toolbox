import base64
import os
import pathlib


def deserialize_str(s):
    return base64.b64decode(s).decode('utf-8')

def set_output(name, value, encode_it=False):
    if isinstance(value, bool):
        value = str(value).lower()
    if encode_it:
        value = base64.b64encode(value.encode('utf-8')).decode('utf-8')
    with open(os.environ['GITHUB_OUTPUT'], 'a') as fh:
        print(f'{name}={value}', file=fh)

def set_env(name, value):
    with open(os.environ.get('GITHUB_ENV', '.env'), 'a') as fh:
        print(f'{name}={value}', file=fh)

def get_output() -> dict:
    output_vars = pathlib.Path(os.getenv('GITHUB_OUTPUT')).read_text()
    return dict(line.strip().split('=', 1) for line in output_vars.splitlines() if line and not line.startswith('#'))