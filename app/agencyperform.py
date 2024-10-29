from flask import Flask, jsonify, render_template, request
from mymodules.core.app_agencyperform import AgencyPerformApp
from mymodules.thisconstants.functions import *
from typing import *
import os

app = Flask(__name__)

local_db_dir = os.path.join(os.path.dirname(
    os.path.dirname(__file__)
    ), 'db')

@app.route('/')
def index():
    return render_template('index_2ap.html')

@app.route('/init_db', methods=['GET'])
def init_db():
    try:
        remote_db_dir = load_yaml(os.path.join(local_db_dir, 'conn.yaml'))['remote']
        AgencyPerformApp().start(local_db_dir=local_db_dir, 
                              remote_db_dir=remote_db_dir)
        
        return jsonify({"message":'OK'}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/search_employee/<string:query>/<string:mode>', methods=['GET'])
def search_employee(query, mode):
    try:
        response_data = AgencyPerformApp().select_target_employee(query=query, 
                                                                  mode=mode)

        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/get_table', methods=['GET'])
def get_table():
    try:
        response_data = AgencyPerformApp().get_performance()

        return jsonify(response_data), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500 
    
if __name__ == '__main__':
    app.run(debug=True)