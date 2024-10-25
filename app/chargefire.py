from flask import Flask, jsonify, render_template, request
from mymodules.core.app_chargefire import ChargeFireApp
from typing import *
import os
import yaml

app = Flask(__name__)

local_db_dir = os.path.join(os.path.dirname(
    os.path.dirname(__file__)
    ), 'db')

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

        final_response = merge_responses(responses)

        worst = ChargeFireApp().worst_pairs()
        for pair in final_response['pairs']:
            if pair['employee_code'] in worst['worst']:
                pair['selected'] = True
        print(final_response)
        
        return jsonify(final_response), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route('/generate_excel_tables/<string:banned_pairs>', methods=['GET'])
def generate_excel_tables(banned_pairs):
    try:
        banned_list = banned_pairs.split(',')
        response_data = ChargeFireApp().prebuild_tables(banned_list)
        return jsonify({response_data}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)