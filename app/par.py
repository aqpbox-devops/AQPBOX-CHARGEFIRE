from flask import Flask, jsonify, render_template, request
from app.mymodules.core.chargefire_core import AppChargeFireCore
import os

app = Flask(__name__)

local_db_dir = os.path.join(os.path.dirname(
    os.path.dirname(__file__)
    ), 'db')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init_db/<path:directory>', methods=['GET'])
def init_db(directory):
    try:
        AppChargeFireCore().start(local_db_dir=local_db_dir, 
                                  remote_db_dir=directory)
        
        return jsonify({"message":'OK'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/search_employee/<string:query>/<string:mode>', methods=['GET'])
def search_employee(query, mode):
    try:
        response_data = AppChargeFireCore().select_target_employee(query=query, 
                                                                   mode=mode)

        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500