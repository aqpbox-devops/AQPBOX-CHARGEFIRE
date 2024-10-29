import warnings

warnings.filterwarnings("ignore")

from mymodules.core.appcore import singleton, AppCore
from mymodules.database.sqlite_handler import to_snapshot_getter
from mymodules.core.employee import EmployeeCapture
from mymodules.thisconstants.vars import *
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import *

LSUMMARY = 'Avance hasta hoy'
LBALANCE = 'Saldo'
LGROWTH = 'Crecimiento'
LGOAL = 'Meta'
LDIFF = 'Diferencia'
LCOMPL = '% Cumplimiento'
LNUMBERING = 'No.'
LRETENTION = '% Retencion'
LPAY2DATE = '% Pago a Hoy'
LOVERDUE = 'Mora SBS'
LTOTAL = 'Total'
LQUALIFIER = 'Calificador'

def div_by_0(n, d):
    return 0 if d == 0 else (n / d)

class MonthDataWriter:
    def __init__(self, month: int, 
                 dfA: pd.DataFrame, 
                 dfB: pd.DataFrame,
                 dfC: pd.DataFrame,
                 dfD: pd.DataFrame,
                 dfE: pd.DataFrame):
        self.id = month
        self.A = dfA
        self.B = dfB
        self.C = dfC
        self.D = dfD
        self.E = dfE
        
    def add2A(self, balance, growth, goal):
        row = [balance, growth, goal]
        difference = growth - goal
        compliance = div_by_0(growth, goal)

        row += [difference, compliance]

        self.A.loc[self.id] = row

    def add2B(self, clients, growth, goal):
        row = [clients, growth, goal]
        difference = growth - goal
        compliance = div_by_0(growth, goal)

        row += [difference, compliance]

        self.B.loc[self.id] = row

    def add2C(self, kpi):
        self.C.loc[self.id] = [kpi, kpi / 25.0]

    def add2D(self, retention, payment_to_date, sbs):
        self.D.loc[self.id] = [retention, payment_to_date, sbs]

    def add2E(self, score, qualifier):
        self.E.loc[self.id] = [score, qualifier]

class FinalReportData:
    def __init__(self, name, 
                 code, 
                 user, 
                 category, 
                 region,
                 zone,
                 agency,
                 committee, 
                 hire_date):
        self.name = name
        self.code = code
        self.user = user
        self.category = category
        self.region = region
        self.zone = zone
        self.agency = agency
        self.committee = committee
        diff = relativedelta(datetime.fromtimestamp(int(hire_date)), datetime.now())
        self.longevity = abs(diff.years) * 12 + abs(diff.months)

        all_months = [i for i in range(1, 13)]
        all_months += [LSUMMARY]

        self.A = pd.DataFrame(index=all_months, columns=[LBALANCE, LGROWTH, LGOAL, LDIFF, LCOMPL])
        self.B = pd.DataFrame(index=all_months, columns=[LNUMBERING, LGROWTH, LGOAL, LDIFF, LCOMPL])
        self.C = pd.DataFrame(index=all_months, columns=[LNUMBERING, LCOMPL])
        self.D = pd.DataFrame(index=all_months, columns=[LRETENTION, LPAY2DATE, LOVERDUE])
        self.E = pd.DataFrame(index=all_months, columns=[LTOTAL, LQUALIFIER])

    def add_month(self, row: pd.DataFrame):
        try:
            print(type(row), row)
            month = MonthDataWriter(row['month_number'],
                            self.A, self.B, self.C, self.D, self.E)
            
            month.add2A(row['sadm'], row['vmcbm'], row['smeta'])
            month.add2B(row['sadc'], row['vmcbc'], row['cmeta'])
            month.add2C(row['kpi_top'])
            month.add2D(row['retention'], row['spph_'], row['sbs'])
            month.add2E(row['score'], row['quali'])

            self.A.fillna(0, inplace=True)
            self.B.fillna(0, inplace=True)
            self.C.fillna(0, inplace=True)
            self.D.fillna(0, inplace=True)
            self.E.fillna(0, inplace=True)

        except KeyError:
            print('Key not found.')

    def calculate_summary(self):
        summA = {}
        summB = {}
        summC = {}
        summD = {}
        summE = {}

        summA[LBALANCE] = self.A.loc[self.A[LBALANCE].last_valid_index(), LBALANCE]
        summA[LGROWTH] = self.A[LGROWTH].sum()
        summA[LGOAL] = self.A[LGOAL].sum()
        summA[LDIFF] = self.A[LDIFF].sum()
        summA[LCOMPL] = div_by_0(summA[LGOAL], summA[LDIFF])

        summB[LNUMBERING] = self.B.loc[self.B[LNUMBERING].last_valid_index(), LNUMBERING]
        summB[LGROWTH] = self.B[LGROWTH].sum()
        summB[LGOAL] = self.B[LGOAL].sum()
        summB[LDIFF] = self.B[LDIFF].sum()
        summB[LCOMPL] = div_by_0(summB[LGOAL], summB[LDIFF])

        summC[LNUMBERING] = div_by_0(self.C[LNUMBERING].sum(), 
                                        ((self.C[LNUMBERING].notna()) & (self.C[LNUMBERING] != 0)).sum())
        summC[LCOMPL] = div_by_0(summC[LNUMBERING], 25.0)

        summD[LRETENTION] = div_by_0(self.D[LRETENTION].sum(), 
                                        ((self.D[LRETENTION].notna()) & (self.D[LRETENTION] != 0)).sum())
        summD[LPAY2DATE] = div_by_0(self.D[LPAY2DATE].sum(), 
                                        ((self.D[LPAY2DATE].notna()) & (self.D[LPAY2DATE] != 0)).sum())
        summD[LOVERDUE] = self.D.loc[self.D[LOVERDUE].last_valid_index(), LOVERDUE]
        summE[LTOTAL] = self.E[LTOTAL].mean(skipna=True)
        summE[LQUALIFIER] = get_description(summE[LTOTAL])

        self.A.loc[LSUMMARY] = summA
        self.B.loc[LSUMMARY] = summB
        self.C.loc[LSUMMARY] = summC
        self.D.loc[LSUMMARY] = summD
        self.E.loc[LSUMMARY] = summE

    def to_dict(self):
        report_dict = {
            'names': self.name,
            'employee_code': str(self.code),
            'username': self.user,
            'category': self.category,
            'region': self.region,
            'zone': self.zone,
            'agency': self.agency,
            'committee': self.committee,
            'longevity': str(self.longevity),
            'data': {
                'A': self._convert_keys_to_strings(self.A.to_dict(orient='index')),
                'B': self._convert_keys_to_strings(self.B.to_dict(orient='index')),
                'C': self._convert_keys_to_strings(self.C.to_dict(orient='index')),
                'D': self._convert_keys_to_strings(self.D.to_dict(orient='index')),
                'E': self._convert_keys_to_strings(self.E.to_dict(orient='index'))
            }
        }
        
        return report_dict

    def _convert_keys_to_strings(self, data_dict):
        return {str(key): value for key, value in data_dict.items()}

@singleton
class AgencyPerformApp(AppCore):
    def __init__(self):
        super().__init__()
    
    def get_performance(self):

        response = {'target': {}}

        if self.target_employee is not None:

            now = datetime.now()
            since = datetime(year=now.year, month=1, day=1)

            frequency_snapshot = to_snapshot_getter((since, now))

            query = f'''
            SELECT *
            FROM R017_327
            WHERE employee_code = {self.target_employee.employee_code}
            AND {frequency_snapshot};
            '''

            df = self.connection.fetch_all(query)

            df.sort_values(by='snapshot_date', inplace=True)

            df['month_number'] = pd.to_datetime(df['snapshot_date'], unit='s').dt.month

            print(df)

            head = df.iloc[0]

            data = FinalReportData(head['names'], head['employee_code'], head['username'], 
                                   head['category'], head['region'], head['zone'], 
                                   head['agency'], head['committee'], head['hire_date'])
    
            for idx, row in df.iterrows():
                data.add_month(row)

            data.calculate_summary()

            response['target'] = data.to_dict()

        return response



if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)
    AgencyPerformApp().start('C:\\Users\\IMAMANIH\\Documents\\GithubRepos\\AQPBOX-CHARGEFIRE\\db',
                          '\\\\Info7352\\aper\\R327-R017(BASE)')
    
    print(AgencyPerformApp().select_target_employee('aquispej', 'username'))

    print(AgencyPerformApp().get_performance())

