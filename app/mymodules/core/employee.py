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
        self.growth_s = 0
        self.cmeta = 0
        self.growth_c = 0
        self.pmeta = 0
        self.productivity = 0

    def set_numbers(self, *values: int) -> None:
        if len(values) != 6:
            raise ValueError("Insuficient values -> required 6.")
        
        self.smeta, self.growth_s, self.cmeta, self.growth_c, self.pmeta, self.productivity = values

    def to_dict(self) -> Dict[str, Any]:
        return {
            'employee_code': self.employee_code,
            'employee_dni': self.employee_dni,
            'username': self.username.upper(),
            'names': self.names.title(),
            'hire_date': self.hire_date.strftime('%d/%m/%Y'),
            'selected': self.selected,
            'smeta': self.smeta,
            'growth_s': self.growth_s,
            'cmeta': self.cmeta,
            'growth_c': self.growth_c,
            'pmeta': self.pmeta,
            'productivity': self.productivity,
        }
    