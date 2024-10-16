from flask import Flask, jsonify, render_template, request
from mymodules.database.sqlite_handler import BANTOTALRecordsSQLiteConnection

app = Flask(__name__)

db_connection = BANTOTALRecordsSQLiteConnection(dir=r'C:\Users\IMAMANIH\Documents\GithubRepos\AQPBOX-CHARGEFIRE\test')

def on_reload():
    db_connection.connect()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init_db/<path:directory>', methods=['GET'])
def init_db(directory):
    try:
        db_connection.copy_from(directory)
        if not db_connection.connect():
            raise ConnectionError("Failed to connect to the database")
        
        return jsonify({"message": db_connection.info().
                        replace('\t', '  ')}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/search_employee/<string:query>/<string:mode>', methods=['GET'])
def search_employee(query, mode):
    try:
        response_data = {
            'employees': []
        }

        if mode != 'code':
            results = db_connection.get_codes_ocurrences_by(query, mode)
            employees = db_connection.get_employees_by_codes(results)

        else:
            employees = db_connection.get_employees_by_codes([query])

        dict_employees = [o.to_dict() for o in employees]

        response_data['employees'] = dict_employees

        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)