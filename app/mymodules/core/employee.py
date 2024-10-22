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

    def to_dict(self) -> Dict[str, Any]:
        return {
            'employee_code': self.employee_code,
            'employee_dni': self.employee_dni,
            'username': self.username.upper(),
            'names': self.names.title(),
            'hire_date': self.hire_date.strftime('%d/%m/%Y'),
            'selected': self.selected
        }
    