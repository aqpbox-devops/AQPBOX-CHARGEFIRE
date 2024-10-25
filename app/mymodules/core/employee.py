from typing import *
from datetime import datetime

import pandas as pd

class EmployeeCapture:
    def __init__(self, employee_code: int, employee_dni: int, 
                 username: str, names: str, hire_date: datetime) -> None:
        self.employee_code = employee_code
        self.employee_dni = employee_dni
        self.username = username
        self.names = names
        self.hire_date = hire_date
        self.selected = False
        self.smeta = 0
        self.vmcbm = 0
        self.cmeta = 0
        self.vmcbc = 0
        self.pmeta = 0
        self.donton = 0

    def set_numbers(self, *values: int) -> None:
        if len(values) != 6:
            raise ValueError("Insuficient values -> required 6.")
        
        self.smeta, self.vmcbm, self.cmeta, self.vmcbc, self.pmeta, self.donton = values

    def to_dict(self) -> Dict[str, Any]:
        return {
            'employee_code': self.employee_code,
            'employee_dni': self.employee_dni,
            'username': self.username.upper(),
            'names': self.names.title(),
            'hire_date': self.hire_date.strftime('%d/%m/%Y'),
            'selected': self.selected,
            'smeta': self.smeta,
            'vmcbm': self.vmcbm,
            'cmeta': self.cmeta,
            'vmcbc': self.vmcbc,
            'pmeta': self.pmeta,
            'donton': self.donton,
        }
    