from flask import Flask, jsonify, render_template, request
from mymodules.core.app_chargefire import ChargeFireApp
from mymodules.core.excel_builder import build_tables
from datetime import datetime
from typing import *
import os
import yaml

app = Flask(__name__)

local_db_dir = os.path.join(os.path.dirname(
    os.path.dirname(__file__)
    ), 'db')

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init_db', methods=['GET'])
def init_db():
    try:
        remote_db_dir = load_yaml(os.path.join(local_db_dir, 'conn.yaml'))['remote']
        ChargeFireApp().start(local_db_dir=local_db_dir, 
                              remote_db_dir=remote_db_dir)
        
        return jsonify({"message":'OK'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/search_employee/<string:query>/<string:mode>', methods=['GET'])
def search_employee(query, mode):
    try:
        response_data = ChargeFireApp().select_target_employee(query=query, 
                                                               mode=mode)

        return jsonify(response_data), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/search_pairs', methods=['POST'])
def search_pairs():
    try:
        flags = request.json
        responses: List[Dict[str, Any]] = []
        responses.append(ChargeFireApp().pick_pairs(flags=flags))
        responses.append(ChargeFireApp().rank_pairs())
        responses.append(ChargeFireApp().prebuild_tables(get_full_target_avg=True))

        final_response = merge_responses(responses)

        worst = ChargeFireApp().worst_pairs()
        for pair in final_response['pairs']:
            if pair['employee_code'] in worst['worst']:
                pair['selected'] = True
        
        return jsonify(final_response), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/generate_excel_tables/<string:banned_pairs>', methods=['GET'])
def generate_excel_tables(banned_pairs):
    try:
        banned_list = banned_pairs.split(',')

        if banned_list[0] == ' ':
            banned_list = None

        response_data = ChargeFireApp().prebuild_tables(banned_list)
        #print(response_data)
        fn = ChargeFireApp().target_employee.names.replace(' ', '_')
        fn += datetime.now().strftime('_(%d-%m-%Y).xlsx')
        
        full_download_path = download_dir(fn)

        build_tables(response_data, full_download_path)
        return jsonify({'xlsx_path': full_download_path}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)