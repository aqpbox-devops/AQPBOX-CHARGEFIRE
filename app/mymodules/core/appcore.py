def singleton(cls):
    instances = {}
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance

from mymodules.core.employee import EmployeeCapture
from mymodules.thisconstants.vars import *
from mymodules.database.sqlite_handler import BANTOTALRecordsSQLiteConnection
from typing import *

class AppCore:
    def __init__(self):
        self.connection: BANTOTALRecordsSQLiteConnection = None
        self.target_employee: EmployeeCapture = None

    def start(self, local_db_dir: str, remote_db_dir) -> None:
        self.connection = BANTOTALRecordsSQLiteConnection(dir=local_db_dir)

        self.connection.copy_from(dir=remote_db_dir)
        if not self.connection.connect():
            raise ConnectionError("Failed to connect to the database")
        
    def select_target_employee(self, query: str, 
                               mode: Literal['code', 
                                             'dni',
                                             'username', 
                                             'fullname']) -> Dict[str, list]:
        if mode == 'username' or mode == 'fullname':
            results = self.connection.get_codes_ocurrences_by(query, mode)
            employees = self.connection.get_employees_by(results)

        else:
            column = 'employee_code' if mode == 'code' else 'employee_dni'
            employees = self.connection.get_employees_by([query], column)

        if len(employees) == 1:
            self.target_employee = employees[0]
            self.target_employee.selected = True

        else:
            self.target_employee = None

        dict_employees = [o.to_dict() for o in employees]

        response_data = {
            'employees': dict_employees
        }

        return response_data