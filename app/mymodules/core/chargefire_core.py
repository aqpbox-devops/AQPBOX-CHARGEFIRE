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
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus, LpBinary, value
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

        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
            
        def pick_worst_pairs(critical_indicators, target_average, pairs_average):
            def euclidean_distance(a, b):
                return np.sqrt(np.sum((a - b) ** 2))
            
            target_mean = target_average[critical_indicators].mean().values
    
            # Inicializar una lista de empleados a eliminar
            employees_to_remove = []
            
            # Calcular el promedio inicial de los empleados
            remaining_employees = pairs_average.copy()
            
            while True:
                # Calcular el promedio de los empleados restantes
                current_mean = remaining_employees[critical_indicators].mean().values
                
                # Verificar si ya se cumple la condición
                if all(current_mean < target_mean):
                    break  # Salir si ya se cumple la condición
                
                best_employee = None
                best_distance = float('inf')
                
                # Evaluar cada empleado para ver si su eliminación mejora la situación
                for index, row in remaining_employees.iterrows():
                    # Crear un nuevo DataFrame sin el empleado actual
                    new_remaining = remaining_employees.drop(index)
                    new_mean = new_remaining[critical_indicators].mean().values
                    
                    # Comprobar si la nueva media es mejor
                    if all(new_mean < target_mean):
                        best_employee = index
                        break  # No necesitamos seguir buscando si encontramos uno que cumple
                    
                    # Calcular la distancia euclidiana
                    new_distance = euclidean_distance(new_mean, target_mean)
                    
                    # Si la nueva distancia es mejor, actualizar mejor opción
                    if new_distance < best_distance:
                        best_distance = new_distance
                        best_employee = index
                
                # Si encontramos un mejor empleado para eliminar, actualizamos
                if best_employee is not None:
                    employees_to_remove.append(best_employee)
                    remaining_employees = remaining_employees.drop(best_employee)
                else:
                    break  # No se encontró mejor opción

            return pairs_average.iloc[employees_to_remove]['employee_code'].tolist()

        if self.paired_employees is not None and self.target_employee is not None:

            filter_columns = []
            for column, flags in self.filter_flags.items():
                if flags['active'] and column in ['region', 'zone', 'agency', 'category']:
                    filter_columns.append(column)

            conflict_mask = self.paired_employees.groupby('employee_code')[filter_columns].nunique()

            conflicting_employees = conflict_mask[conflict_mask.gt(1).any(axis=1)].index.tolist()

            self.paired_employees = self.paired_employees[~self.paired_employees['employee_code'].isin(conflicting_employees)]

            #x MONTH
            critical_indicators = ['smeta', 'growth_s', 'cmeta', 'growth_c', 
                                   'pmeta', 'productivity']
            
            critical_df = self.paired_employees[['employee_code', 'snapshot_date'] + critical_indicators]
            
            target = critical_df.query(f'employee_code == {self.target_employee.employee_code}')
            pairs = critical_df.query(f'employee_code != {self.target_employee.employee_code}')

            target_average = target.groupby('snapshot_date')[critical_indicators].mean().reset_index()

            pairs_average = pairs.groupby(['snapshot_date', 'employee_code'])[critical_indicators].mean().reset_index()
            
            comparison = target_average[critical_indicators] > pairs_average[critical_indicators].mean()
            
            print(target_average)
            print(pairs_average)

            print(comparison)
            n = len(pairs_average)

            if comparison.any().any():
                worst_pairs = pick_worst_pairs(critical_indicators, target_average, pairs_average)
                pairs_average = pairs_average[~pairs_average['employee_code'].isin(worst_pairs)]

            comparison = target_average[critical_indicators] > pairs_average[critical_indicators].mean()
            print(len(pairs_average), n)
            print(comparison)




