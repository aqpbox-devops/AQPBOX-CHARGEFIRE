from flask import Flask, jsonify, render_template, request
from mymodules.database.sqlite_handler import BANTOTALRecordsSQLiteConnection

app = Flask(__name__)

db_connection = BANTOTALRecordsSQLiteConnection(dir=r'C:\Users\IMAMANIH\Documents\GithubRepos\AQPBOX-CHARGEFIRE\test')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init_db/<path:directory>', methods=['GET'])
def init_db(directory):
    try:
        db_connection.copy_from(directory)
        if not db_connection.connect():
            raise ConnectionError("Failed to connect to the database")
        
        return jsonify({"message": "Database initialized successfully.", 
                        "info": db_connection.info().replace('\n', '<br>')}), 200
    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
@app.route('/search/<string:query>/<string:mode>', methods=['GET'])
def search(query, mode):
    try:
        results = db_connection.get_employee_code_by(query, mode)
        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Error during search: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)