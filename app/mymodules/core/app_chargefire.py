import warnings

warnings.filterwarnings("ignore")

from mymodules.core.appcore import singleton, AppCore
from mymodules.database.sqlite_handler import to_snapshot_getter
from mymodules.core.employee import EmployeeCapture
from mymodules.thisconstants.vars import *
import pandas as pd
import numpy as np
from datetime import datetime
from typing import *

@singleton
class ChargeFireApp(AppCore):
    def __init__(self):
        super().__init__()
        self.paired_employees: pd.DataFrame = None
        self.filters_sql: Dict[str, str] = {
            'region': 'region=(SELECT region FROM {})',
            'zone': 'zone=(SELECT zone FROM {})',
            'agency': 'agency=(SELECT agency FROM {})'
        }
        self.critical_indicators = {'growth_s': 1.0, 'growth_c': 0.5, 'productivity': 0.3}

    def target_and_pairs(self, other_columns: List[str] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:

        if self.paired_employees is None:
            return None, None
        
        cols = list(self.critical_indicators.keys())
        cols += ['smeta', 'cmeta', 'pmeta']

        if other_columns is not None:
            cols += other_columns

        critical_df = self.paired_employees[['employee_code', 'snapshot_date'] + cols]
            
        target = critical_df.query(f'employee_code == {self.target_employee.employee_code}')
        pairs = critical_df.query(f'employee_code != {self.target_employee.employee_code}')

        return target, pairs
    
    def pick_pairs(self, flags: Dict[str, bool]) -> Dict[str, Any]:

        response_data = {'pairs': []}

        if self.target_employee is not None:

            any_true = False

            filters: List[str] = []

            frequency_snapshot = to_snapshot_getter((datetime.strptime(flags['start_date'], "%Y-%m-%d"), 
                                                     datetime.strptime(flags['end_date'], "%Y-%m-%d")))
            
            for key, value in flags.items():
                if key.endswith('date'):
                    continue
                any_true |= value
                if value:
                    filters.append(self.filters_sql[key])

            query = f'''
            WITH TargetEmployee AS (
                SELECT *
                FROM R017_327
                WHERE employee_code = {self.target_employee.employee_code}
                AND {frequency_snapshot}
            )
            SELECT *
            FROM R017_327
            WHERE category=(SELECT category FROM TargetEmployee)
            AND (cmeta=(SELECT cmeta FROM TargetEmployee) 
                AND smeta=(SELECT smeta FROM TargetEmployee) 
                AND pmeta=(SELECT pmeta FROM TargetEmployee))
            AND worked_days > 14
            AND {frequency_snapshot}
            AND {'\nAND '.join([filter.format(*(['TargetEmployee']*(filter.count('{}')))) for filter in filters])}
            GROUP BY employee_code;'''

            if any_true:
                self.paired_employees = self.connection.fetch_all(query)

                target_employee_data = self.paired_employees[self.paired_employees['employee_code'] == self.target_employee.employee_code]

                mutable_columns = ['region', 'zone', 'agency', 'category']
                
                target_employee_data = target_employee_data.sort_values(by='snapshot_date', ascending=False)

                dates_to_remove = set()

                for _, row in target_employee_data.iterrows():
                    snapshot_date = row['snapshot_date']
                    
                    changes_detected = any(
                        (self.paired_employees[self.paired_employees['snapshot_date'] == snapshot_date][col].nunique() > 1)
                        for col in mutable_columns
                    )
                    
                    if changes_detected:
                        dates_to_remove.add(snapshot_date)

                self.paired_employees = self.paired_employees[~self.paired_employees['snapshot_date'].isin(dates_to_remove)]

                conflict_mask = self.paired_employees.groupby('employee_code')[mutable_columns].nunique()

                conflicting_employees = conflict_mask[conflict_mask.gt(1).any(axis=1)].index.tolist()

                self.paired_employees = self.paired_employees[~self.paired_employees['employee_code'].isin(conflicting_employees)]

                last_employee_code = -1

                cols = list(self.critical_indicators.keys())

                for row in self.paired_employees.itertuples(index=True):
                    if row.employee_code == self.target_employee.employee_code:
                        response_data['target_info'] = {
                            'category': row.category, 
                            'region': row.region, 
                            'zone': row.zone, 
                            'agency': row.agency,
                            'worked_days': row.worked_days
                        }
                        continue

                    if last_employee_code != row.employee_code:
                        pair_code = int(row.employee_code)
                        new_pair = EmployeeCapture(pair_code, 
                                                   int(row.employee_dni), 
                                                   row.username, 
                                                   row.names, 
                                                   datetime.fromtimestamp(int(row.hire_date)))
                        
                        pair_info = self.paired_employees.query(f'employee_code == {pair_code}')[cols + ['smeta', 'cmeta', 'pmeta']].mean(axis=0)
                        print(pair_info.info())
                        new_pair.set_numbers(pair_info['growth_s'], pair_info['smeta'],
                                             pair_info['growth_c'], pair_info['cmeta'],
                                             pair_info['productivity'], pair_info['pmeta'])
                        response_data['pairs'].append(new_pair)

                        last_employee_code = row.employee_code

        response_data['pairs'] = [emp.to_dict() for emp in response_data['pairs']]

        return response_data
    
    def rank_pairs(self) -> Dict[str, Any]:

        response_data = {'ranks': {}}

        if self.paired_employees is not None and self.target_employee is not None:
            for indicator in self.critical_indicators:
                ranked_indices = self.paired_employees[indicator].rank().astype(int)
                sorted_employee_codes = self.paired_employees.loc[ranked_indices.sort_values().index, 'username'].tolist()
                response_data['ranks'][indicator] = sorted_employee_codes
                
        return response_data
    
    def worst_pairs(self) -> Dict[str, Any]:

        response_data = {'worst': []}

        if self.paired_employees is not None and self.target_employee is not None:

            target, pairs = self.target_and_pairs()

            cols = list(self.critical_indicators.keys())

            target_average = target.groupby('snapshot_date')[cols].mean().reset_index()

            pairs_average = pairs.groupby(['snapshot_date', 'employee_code'])[cols].mean().reset_index()
            
            comparison = target_average[cols] > pairs_average[cols].mean()

            if comparison.any().any():

                pairs['weighted_sum'] = (pairs['growth_s'] * self.critical_indicators['growth_s'] +
                                         pairs['growth_c'] * self.critical_indicators['growth_c'] +
                                         pairs['productivity'] * self.critical_indicators['productivity'])

                threshold = pairs['weighted_sum'].quantile(1/3)

                response_data['worst'] = pairs[pairs['weighted_sum'] < threshold]['employee_code'].tolist()

        return response_data

    def prebuild_tables(self, banned_pairs: List[str]=None) -> Dict[str, Any]:

        def every_month_of(monthly_averages: pd.DataFrame, force_mean=False):
            snapshots_list = []

            df = monthly_averages

            if df.empty:
                return snapshots_list

            if force_mean:
                df = monthly_averages.mean(numeric_only=True)
                df = pd.DataFrame([df])
                df['snapshot_date_t'] = pd.to_datetime(df['snapshot_date'], unit='s')

            for index, row in df.iterrows():
                snapshot_dict = {
                    'month': MONTHS_SPANISH[row['snapshot_date_t'].month], 
                    'smeta': row['smeta'], 
                    'growth_s': row['growth_s'], 
                    'cmeta': row['cmeta'], 
                    'growth_c': row['growth_c'], 
                    'pmeta': row['pmeta'], 
                    'productivity': row['productivity']
                }
                snapshots_list.append(snapshot_dict) 

            return snapshots_list

        response_data = {'tables': {}}

        tables_dict = {}

        if self.paired_employees is not None and self.target_employee is not None:
            target, pairs = self.target_and_pairs()

            if banned_pairs is not None:
                pairs = pairs[~pairs['employee_code'].isin([int(code) for code in banned_pairs])]

            target['snapshot_date_t'] = pd.to_datetime(target['snapshot_date'], unit='s')
            target_monthly = target.groupby(target['snapshot_date_t'].dt.to_period('M')).mean(numeric_only=True).reset_index()

            pairs['snapshot_date_t'] = pd.to_datetime(pairs['snapshot_date'], unit='s')
            pairs_monthly_averages = pairs.groupby(pairs['snapshot_date_t'].dt.to_period('M')).mean(numeric_only=True).reset_index()

            tables_dict['all_months_target'] = {'username': self.target_employee.username, 
                                                'timeline': every_month_of(target_monthly)}
            
            tables_dict['all_months_pairs_avg'] = {'timeline': every_month_of(pairs_monthly_averages)}

            tables_dict['full_avg_target'] = {'username': self.target_employee.username,
                                              'average': every_month_of(target_monthly, True)}
            
            tables_dict['full_avg_pairs'] = {'average': every_month_of(pairs_monthly_averages, True)}

            tables_dict['pairs_all_months'] = []

            for employee_code in pairs['employee_code'].unique():
                pair = pairs[pairs['employee_code'] == employee_code]

                pair['snapshot_date_t'] = pd.to_datetime(pair['snapshot_date'], unit='s')

                pair_monthly = pair.groupby(pair['snapshot_date_t'].dt.to_period('M')).mean(numeric_only=True).reset_index()

                tables_dict['pairs_all_months'].append({
                    'username': employee_code,
                    'timeline': every_month_of(pair_monthly),
                    'average': every_month_of(pair_monthly, True)
                })
            
        response_data['tables'] = tables_dict

        return response_data

if __name__ == '__main__':
    pd.set_option('display.max_columns', None)
    pd.set_option('display.max_rows', None)
    pd.set_option('display.width', None)
    ChargeFireApp().start('C:\\Users\\IMAMANIH\\Documents\\GithubRepos\\AQPBOX-CHARGEFIRE\\db',
                          '\\\\Info7352\\aper\\R327-R017(BASE)')
    
    print(ChargeFireApp().select_target_employee('aquispej', 'username'))

    print(ChargeFireApp().pick_pairs({'region': True, 'zone': False, 'agency': True, 
                                      'start_date': '2024-09-01', 'end_date': '2024-10-22'}))

    print(ChargeFireApp().rank_pairs())
    print(ChargeFireApp().worst_pairs())

    print(ChargeFireApp().prebuild_tables(['16482']))