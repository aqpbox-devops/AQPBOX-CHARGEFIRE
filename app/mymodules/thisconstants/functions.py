from typing import *
import os
import yaml

def download_dir(fn: str=None) -> str:
    dir = os.path.join(os.path.expanduser("~"), "Downloads")
    return dir if fn is None or fn == '' else os.path.join(dir, fn)

def load_yaml(yaml_path):
    with open(yaml_path, 'r') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config

def merge_responses(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    big_response = {}
    for response in responses:
        for key, value in response.items():
            big_response[key] = value

    return big_response