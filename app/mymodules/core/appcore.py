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
        response_data = {
            'employees': []
        }
        
        column = 'employee_code' if mode != 'dni' else 'employee_dni'

        exact_match = None
        employees: List[EmployeeCapture] = []

        if mode == 'username' or mode == 'fullname':
            results, exact_match = self.connection.get_codes_ocurrences_by(query, mode)
            print('?????', type(results), type(exact_match))
            employees += self.connection.get_employees_by(results)

            if exact_match is not None:
                employees += self.connection.get_employees_by([exact_match], column)

        else:
            employees += self.connection.get_employees_by([query], column)

        if exact_match is not None:
            employees[-1].selected = True
            self.target_employee = employees[-1]

        elif len(employees) == 1:
            employees[0].selected = True
            self.target_employee = employees[0]

        else:
            self.target_employee = None

        dict_employees = [o.to_dict() for o in employees]

        response_data['employees'] = dict_employees

        return response_data