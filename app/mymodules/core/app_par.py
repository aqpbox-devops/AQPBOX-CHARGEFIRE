from mymodules.core.appcore import singleton, AppCore
from mymodules.core.employee import EmployeeCapture
import pandas as pd
from typing import *

@singleton
class ParApp(AppCore):
    def __init__(self):
        super().__init__()