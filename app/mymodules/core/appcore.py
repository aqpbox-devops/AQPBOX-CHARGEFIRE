def singleton(cls):
    instances = {}
    
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance

from mymodules.core.employee import EmployeeCapture
from mymodules.database.sqlite_handler import BANTOTALRecordsSQLiteConnection
from datetime import datetime
from typing import *
import pandas as pd

@singleton
class AppChargeFireCore:
    def __init__(self) -> None:
        self.connection: BANTOTALRecordsSQLiteConnection = None
        self.target_employee: EmployeeCapture = None
        self.paired_employees: pd.DataFrame = None
        self.target_pairs: List[EmployeeCapture] = []

        self.clear_flags()

    def start(self, local_db_dir: str, remote_db_dir) -> None:
        self.connection = BANTOTALRecordsSQLiteConnection(dir=local_db_dir)

        self.connection.copy_from(dir=remote_db_dir)
        if not self.connection.connect():
            raise ConnectionError("Failed to connect to the database")
        
    def clear_flags(self) -> None:
        if not hasattr(self, 'filter_flags'):
            self.filter_flags: Dict[str, Dict[str, bool]] = {
                'region': {'active': False, 'sql': 'region=(SELECT region FROM {})'},
                'zone': {'active': False, 'sql': 'zone=(SELECT region FROM {})'},
                'agency': {'active': False, 'sql': 'agency=(SELECT region FROM {})'},
                'category': {'active': False, 'sql': 'category=(SELECT region FROM {})'},
                'atLeast15': {'active': False, 'sql': 'worked_days>14 --{}'},
                'goal': {'active': False, 'sql': '''(cmeta=(SELECT region FROM {}) 
                         AND smeta=(SELECT region FROM {}) 
                         AND cprod=(SELECT region FROM {}))'''},
            }

        for _, value in self.filter_flags.items():
            value['active'] = False

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

        if len(employees) > 0:
            self.target_employee = employees[0]

        dict_employees = [o.to_dict() for o in employees]

        response_data = {
            'employees': dict_employees
        }

        return response_data
    
    def pick_pairs(self, flags: Dict[str, bool], period: Tuple[datetime, datetime]) -> Dict[str, Any]:

        response_data = {
            'employees': []
        }

        if self.target_employee is not None:

            any_true = False

            filters: List[str] = []

            for key, value in self.filter_flags.items():
                any_true |= flags[key]
                value['active'] = flags[key]
                if value['active']:
                    filters.append(value['sql'])

            if any_true:
                self.paired_employees = self.connection.fetch_by_filters(self.target_employee.employee_code, 
                                                                         'TargetEmployee', filters, period)
                
                response_data['employees'] = [EmployeeCapture(int(row.employee_code), 
                                                              int(row.employee_dni), 
                                                              row.username, 
                                                              row.names, 
                                                              int(row.hire_date.timestamp())
                                                              ) for row in self.paired_employees.itertuples(index=True)]
                last_employee_code = -1
                for row in self.paired_employees.itertuples(index=True):
                    if row.employee_code == self.target_employee.employee_code:
                        continue

                    if last_employee_code != row.employee_code:
                        response_data['employees'].append(EmployeeCapture(int(row.employee_code), 
                                                                          int(row.employee_dni), 
                                                                          row.username, 
                                                                          row.names, 
                                                                          int(row.hire_date.timestamp())))
                        last_employee_code = row.employee_code

                self.target_pairs = response_data['employees']

        return response_data

        