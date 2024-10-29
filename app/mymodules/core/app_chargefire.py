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
            'region': 'region={}',
            'zone': 'zone={}',
            'agency': 'agency={}'
        }
        self.critical_indicators = {'vmcbm': 1.0, 'vmcbc': 0.5, 'donton': 0.3}

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

        if self.target_employee is None:
            return response_data

        daily = False
        frequency_snapshot = to_snapshot_getter((datetime.strptime(flags['start_date'], "%Y-%m-%d"), 
                                                 datetime.strptime(flags['end_date'], "%Y-%m-%d")), 
                                                 daily=daily)

        filters: List[str] = [self.filters_sql[key] for key, value in flags.items() if key not in ['start_date', 'end_date'] and value]

        query = f'''
        WITH TargetEmployee AS (
            SELECT *
            FROM R017_327
            WHERE employee_code = {self.target_employee.employee_code}
            AND {frequency_snapshot}  -- Asegúrate de que esto filtre correctamente por fecha
            ORDER BY snapshot_date DESC  -- Cambia 'snapshot_date' por el nombre real de tu columna de timestamp
        ),
        FilteredTargetEmployee AS (
            SELECT *,
                LAG(region) OVER (ORDER BY snapshot_date DESC) AS prev_region,
                LAG(zone) OVER (ORDER BY snapshot_date DESC) AS prev_zone,
                LAG(agency) OVER (ORDER BY snapshot_date DESC) AS prev_agency,
                LAG(category) OVER (ORDER BY snapshot_date DESC) AS prev_category
            FROM TargetEmployee
        )
        SELECT *
        FROM FilteredTargetEmployee
        WHERE 
            (region = prev_region AND zone = prev_zone AND agency = prev_agency AND category = prev_category)
            OR prev_region IS NULL;  -- Incluye el primer registro donde no hay cambios
        '''

        df = pd.DataFrame(self.connection.fetch_all(query))
        
        if df.empty:
            return response_data
        
        if not df.empty:
            region = df['region'].iloc[0]
            zone = df['zone'].iloc[0]
            agency = df['agency'].iloc[0]
            category = df['category'].iloc[0]

            filters = {key: value.format(f"'{locals()[key]}'") for key, value in self.filters_sql.items() if key in flags and flags[key]}

            active_filter = next(iter(filters.values()))

            query_pairs = f'''
                SELECT *
                FROM R017_327
                WHERE {active_filter}
                AND {frequency_snapshot}
                AND category = '{category}'
                AND worked_days > 14
                AND employee_code != {self.target_employee.employee_code}  -- Excluir al empleado objetivo
            '''

            pairs_df = pd.DataFrame(self.connection.fetch_all(query_pairs))

            target_cmeta = df['cmeta'].mean()
            target_smeta = df['smeta'].mean()
            target_pmeta = df['pmeta'].mean()

            if not pairs_df.empty:
                
                averages_pairs = pairs_df.groupby('employee_code').agg({
                    'employee_dni': 'first',
                    'username': 'first',
                    'names': 'first',
                    'hire_date': 'first',
                    'vmcbm': 'mean',
                    'smeta': 'mean',
                    'vmcbc': 'mean',
                    'cmeta': 'mean',
                    'donton': 'mean',
                    'pmeta': 'mean'
                }).reset_index()

                filtered_pairs = averages_pairs[
                    (averages_pairs['cmeta'] == target_cmeta) &
                    (averages_pairs['smeta'] == target_smeta) &
                    (averages_pairs['pmeta'] == target_pmeta)
                ]

                valid_pairs = pairs_df[pairs_df['employee_code'].isin(filtered_pairs['employee_code'])]

                df = df[valid_pairs.columns]

                self.paired_employees = pd.concat([df, valid_pairs])

                self.paired_employees['smeta'] = self.paired_employees['smeta'].round(1)
                self.paired_employees['vmcbm'] = self.paired_employees['vmcbm'].round(2)
                self.paired_employees['cmeta'] = self.paired_employees['cmeta'].round(1)
                self.paired_employees['vmcbc'] = self.paired_employees['vmcbc'].round(2)
                self.paired_employees['pmeta'] = self.paired_employees['pmeta'].round(1)
                self.paired_employees['donton'] = self.paired_employees['donton'].round(2)

                for _, row in filtered_pairs.iterrows():
                    an_employee_code = int(row['employee_code'])

                    if an_employee_code == self.target_employee.employee_code:
                        continue

                    new_pair = EmployeeCapture(
                        an_employee_code,
                        int(row['employee_dni']),
                        row['username'],
                        row['names'],
                        datetime.fromtimestamp(int(row['hire_date']))
                    )

                    new_pair.set_numbers(
                        round(row['smeta'], 1), round(row['vmcbm'], 2),
                        round(row['cmeta'], 1), round(row['vmcbc'], 2),
                        round(row['pmeta'], 1), round(row['donton'], 2)
                    )

                    response_data['pairs'].append(new_pair.to_dict())

        return response_data
    
    def rank_pairs(self) -> Dict[str, Any]:

        response_data = {'ranks': {}}

        if self.paired_employees is not None and self.target_employee is not None:
            target, pairs = self.target_and_pairs(['username'])

            for indicator in self.critical_indicators:
                averages = pairs.groupby('employee_code')[indicator].mean().reset_index()
                averages = averages.sort_values(by=indicator, ascending=False)

                sorted_employee_codes = pairs[pairs['employee_code'].isin(averages['employee_code'])] \
                    .drop_duplicates(subset='username') \
                    .set_index('employee_code').loc[averages['employee_code']]['username'].tolist()

                response_data['ranks'][indicator] = sorted_employee_codes[::-1]

        return response_data
    
    def worst_pairs(self) -> Dict[str, Any]:
        response_data = {'worst': []}

        if self.paired_employees is not None and self.target_employee is not None:
            target, pairs = self.target_and_pairs()

            cols = list(self.critical_indicators.keys())

            target_average = target.groupby('snapshot_date')[cols].mean().reset_index()

            pairs_average = pairs.groupby('employee_code')[cols].mean().reset_index()

            comparison = target_average[cols].mean() > pairs_average[cols].mean()

            if comparison.any():

                pairs_average['weighted_sum'] = (
                    pairs_average['vmcbm'] * self.critical_indicators['vmcbm'] +
                    pairs_average['vmcbc'] * self.critical_indicators['vmcbc'] +
                    pairs_average['donton'] * self.critical_indicators['donton']
                )

                threshold = pairs_average['weighted_sum'].quantile(1/3)

                response_data['worst'] = pairs_average[pairs_average['weighted_sum'] < threshold]['employee_code'].tolist()

        return response_data

    def prebuild_tables(self, banned_pairs: List[str]=None, 
                        get_full_target_avg: bool=False) -> Dict[str, Any]:

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
                    'month': MONTHS_SPANISH[row['snapshot_date_t'].month].upper(), 
                    'smeta': round(row['smeta'], 1),
                    'vmcbm': round(row['vmcbm'], 2), 
                    'cmeta': round(row['cmeta'], 1),
                    'vmcbc': round(row['vmcbc'], 2), 
                    'pmeta': round(row['pmeta'], 1), 
                    'donton': round(row['donton'], 2)
                }
                snapshots_list.append(snapshot_dict) 

            return snapshots_list

        response_data = {'tables': {}}

        tables_dict = {}

        if self.paired_employees is not None and self.target_employee is not None:
            target, pairs = self.target_and_pairs(['username', 'region', 'zone', 
                                                   'agency', 'category'])

            target_1row= target.iloc[0]

            target_attrs = {
                'region': target_1row['region'],
                'zone': target_1row['zone'],
                'agency': target_1row['agency'],
                'category': target_1row['category']
            }

            if banned_pairs is not None:
                pairs = pairs[~pairs['username'].isin([username for username in banned_pairs])]

            #print(target)

            target['snapshot_date_t'] = pd.to_datetime(target['snapshot_date'], unit='s')
            target_monthly = target.groupby(target['snapshot_date_t'].dt.to_period('M')).mean(numeric_only=True).reset_index()

            tables_dict['full_avg_target'] = {'username': self.target_employee.username,
                                              'average': every_month_of(target_monthly, True)}

            if get_full_target_avg:

                print(tables_dict['full_avg_target'])
                print('INFO TARGET  ', target_attrs)

                tables_dict['full_avg_target']['attrs'] = target_attrs

                print(tables_dict)

                response_data['tables'] = tables_dict

                return response_data

            pairs['snapshot_date_t'] = pd.to_datetime(pairs['snapshot_date'], unit='s')
            pairs_monthly_averages = pairs.groupby(pairs['snapshot_date_t'].dt.to_period('M')).mean(numeric_only=True).reset_index()

            tables_dict['all_months_target'] = {'username': self.target_employee.username, 
                                                'timeline': every_month_of(target_monthly)}
            
            tables_dict['all_months_pairs_avg'] = {'timeline': every_month_of(pairs_monthly_averages)}
            
            tables_dict['full_avg_pairs'] = {'average': every_month_of(pairs_monthly_averages, True)}

            tables_dict['pairs_all_months'] = []

            for employee_code in pairs['employee_code'].unique():
                pair = pairs[pairs['employee_code'] == employee_code]

                pair['snapshot_date_t'] = pd.to_datetime(pair['snapshot_date'], unit='s')

                pair_monthly = pair.groupby(pair['snapshot_date_t'].dt.to_period('M')).mean(numeric_only=True).reset_index()

                tables_dict['pairs_all_months'].append({
                    'username': pair['username'].values[0],
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

    print(ChargeFireApp().pick_pairs({'region': False, 'zone': True, 'agency': False, 
                                      'start_date': '2024-01-01', 'end_date': '2024-10-22'}))

    print(ChargeFireApp().rank_pairs())
    print(ChargeFireApp().worst_pairs())

    print(ChargeFireApp().prebuild_tables())