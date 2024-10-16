from typing import *
from datetime import datetime

class EmployeeCapture:
    def __init__(self, employee_code: int, username: str, 
                 names: str, hire_date: datetime):
        self.employee_code = employee_code
        self.username = username
        self.names = names
        self.hire_date = hire_date

    def to_dict(self) -> Dict[str, Any]:
        return {
            'employee_code': self.employee_code,
            'username': self.username.upper(),
            'names': self.names.title(),
            'hire_date': self.hire_date.strftime('%d/%m/%Y')
        }