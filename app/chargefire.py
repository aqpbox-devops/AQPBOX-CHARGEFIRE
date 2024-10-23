from flask import Flask, jsonify, render_template, request
from mymodules.core.app_chargefire import ChargeFireApp
from typing import *
import os

app = Flask(__name__)

local_db_dir = os.path.join(os.path.dirname(
    os.path.dirname(__file__)
    ), 'db')

#ChargeFireApp().start(local_db_dir=local_db_dir, 
#                      remote_db_dir='\\\\Info7352\\aper\\R327-R017(BASE)')

def merge_responses(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    big_response = {}
    for response in responses:
        for key, value in response.items():
            big_response[key] = value

    return big_response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init_db/<path:directory>', methods=['GET'])
def init_db(directory):
    try:
        ChargeFireApp().start(local_db_dir=local_db_dir, 
                                  remote_db_dir=directory)
        
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
        responses.append(ChargeFireApp().worst_pairs())
        responses.append(ChargeFireApp().rank_pairs())

        return jsonify(merge_responses(responses)), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)