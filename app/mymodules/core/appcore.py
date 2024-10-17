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
from datetime import datetime
from typing import *
import pandas as pd
import numpy as np

@singleton
class AppChargeFireCore:
    def __init__(self) -> None:
        self.connection: BANTOTALRecordsSQLiteConnection = None
        self.target_employee: EmployeeCapture = None
        self.paired_employees: pd.DataFrame = None
        self.target_pairs: List[EmployeeCapture] = []

        self.current_stats: Dict[str, Any] = {
            'by_month': [],
            'by_3months': [],
            'by_6months': [],
        }

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
                'zone': {'active': False, 'sql': 'zone=(SELECT zone FROM {})'},
                'agency': {'active': False, 'sql': 'agency=(SELECT agency FROM {})'},
                'category': {'active': False, 'sql': 'category=(SELECT category FROM {})'},
                'atLeast15': {'active': False, 'sql': 'worked_days>14 --{}'},
                'goals': {'active': False, 'sql': '''(cmeta=(SELECT cmeta FROM {}) 
                         AND smeta=(SELECT smeta FROM {}) 
                         AND pmeta=(SELECT pmeta FROM {}))'''},
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

        if len(employees) == 1:
            self.target_employee = employees[0]

        dict_employees = [o.to_dict() for o in employees]

        response_data = {
            'employees': dict_employees
        }

        return response_data
    
    def pick_pairs(self, flags: Dict[str, bool]) -> Dict[str, Any]:

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
                                                                         'TargetEmployee', 
                                                                         filters, (datetime.strptime(flags['start_date'], "%Y-%m-%d"), 
                                                                                   datetime.strptime(flags['end_date'], "%Y-%m-%d")))
                last_employee_code = -1
                print(self.paired_employees.head(20))
                self.compare_and_fit_pairs()
                for row in self.paired_employees.itertuples(index=True):
                    if row.employee_code == self.target_employee.employee_code:
                        continue

                    if last_employee_code != row.employee_code:
                        response_data['employees'].append(EmployeeCapture(int(row.employee_code), 
                                                                          int(row.employee_dni), 
                                                                          row.username, 
                                                                          row.names, 
                                                                          datetime.fromtimestamp(int(row.hire_date))))
                        last_employee_code = row.employee_code

                self.target_pairs = response_data['employees']

        response_data['employees'] = [emp.to_dict() for emp in response_data['employees']]

        return response_data

    def compare_and_fit_pairs(self) -> None:
        def get_description(score):
            result = QUALI_LOOKUP[(QUALI_LOOKUP['min_value'] <= score) & (QUALI_LOOKUP['max_value'] >= score)]
            
            if not result.empty:
                return result['description'].values[0]
            else:
                return 'Out of range'
        
        if self.paired_employees is not None and self.target_employee is not None:

            grouped_by_snapshot = self.paired_employees.groupby('snapshot_date')#should be 1 row per employee (x snapshot)

            for idx, group in grouped_by_snapshot:
                numerics = group.select_dtypes(include=[np.number])
                target = numerics.query(f'employee_code == {self.target_employee.employee_code}')#Series
                others = numerics.query(f'employee_code != {self.target_employee.employee_code}')#DataFrame

                print('*'*30)
                print(numerics)
                print(target)
                print(others)
                print('*'*30)

                pairs_avg = others.mean()

                comparison = target > pairs_avg

                print(comparison, pairs_avg)