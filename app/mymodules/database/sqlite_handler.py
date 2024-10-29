import shutil

def _copyfileobj_patched(fsrc, fdst, length=16*1024*1024):
    while 1:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)

shutil.copyfileobj = _copyfileobj_patched

import sqlite3
import pickle
import pandas as pd
from datetime import datetime, timedelta
from typing import *
from mymodules.database.indexers import CharTrieIndexer
from mymodules.core.employee import EmployeeCapture
from mymodules.thisconstants.vars import *
from threading import Lock
import os
import io

search_employee_lock = Lock()

def valid_file(a_path: str) -> bool:
    return os.path.exists(a_path)

def make_exist(dir_path):
    this_dir = os.path.dirname(dir_path)
    
    if not valid_file(this_dir):
        os.makedirs(this_dir)

    return dir_path

def blob_to_series(blob: bytes) -> pd.Series:
    return pickle.load(io.BytesIO(blob))

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if len(df.columns) < 2:
        raise ValueError("El DataFrame debe tener al menos dos columnas")

    last_two_columns = df.columns[-2:]

    result_df = df.drop(columns=last_two_columns).copy()

    for index, row in df.iterrows():
        for col in last_two_columns:
            try:
                sub_series = blob_to_series(row[col])

                for sub_col, value in sub_series.items():
                    result_df.at[index, sub_col] = value
            except Exception as e:
                print(f"Error reading BLOB at col {col}, row {index}: {str(e)}")

    return result_df

def get_last_days_of_months(start_date: datetime, end_date: datetime) -> List[int]:
    last_days = []
    current_date = start_date

    while current_date <= end_date:
        if current_date.month == 12:
            next_month = 1
            next_year = current_date.year + 1
        else:
            next_month = current_date.month + 1
            next_year = current_date.year
        
        current_date = current_date.replace(year=next_year, month=next_month, day=1)
        
        last_day_of_previous_month = current_date - timedelta(days=1)
        
        if last_day_of_previous_month <= end_date:
            last_days.append(int(last_day_of_previous_month.timestamp()))

    print(last_days)

    return last_days

def to_snapshot_getter(period: Tuple[datetime, datetime], daily: bool=False) -> str:
    if daily:
        return f"({int(period[0].timestamp())} >= snapshot_date AND snapshot_date <= {int(period[1].timestamp())})"

    else:
        last_days_of_months = get_last_days_of_months(period[0], period[1])
        return f"snapshot_date IN ({', '.join([str(date) for date in last_days_of_months])})"

class BANTOTALRecordsSQLiteConnection:
    def __init__(self, dir: str, db_name: str = 'BANTOTAL(R)327-017.sqlite') -> None:
        self.db_path = make_exist(os.path.join(dir, db_name))
        self.connection = None
        self.cursor = None
        self.indexer_username = None
        self.indexer_names = None
        self.indexer_username = CharTrieIndexer(self.db_path.replace('.sqlite', 
                                                                     '_idx_usernames.pkl'))
        self.indexer_names = CharTrieIndexer(self.db_path.replace('.sqlite', 
                                                                  '_idx_names.pkl'))

    def connect(self) -> bool:

        if not valid_file(self.db_path):
            return False
        
        if self.connection is None:

            self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
            if self.connection is not None:
                self.cursor = self.connection.cursor()

            self.load_indexers()

        return True

    def close(self):

        self.connection.close()

    def load_indexers(self) -> None:
        if self.indexer_username is not None:
            self.indexer_username.load_from_file()

        if self.indexer_names is not None:
            self.indexer_names.load_from_file()

    def info(self) -> str:
        str_repr = f"[{'='*50}]\n"
        db_size = os.path.getsize(self.db_path) / (1024 * 1024)
        str_repr += f"|-DB size: {db_size:.2f} MB\n"

        self.cursor.execute("SELECT COUNT(DISTINCT employee_code) FROM R017_327")
        num_employees = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(DISTINCT snapshot_date) FROM R017_327")
        num_snapshots = self.cursor.fetchone()[0]

        self.cursor.execute("""
            SELECT snapshot_date, COUNT(r017_data), COUNT(r327_data) AS blob_count
            FROM R017_327
            GROUP BY snapshot_date
        """)
        
        blob_counts = self.cursor.fetchall()

        str_repr += f"|-Blobs per Snapshot:\n"
        for snapshot_int, r017_count, r327_count in blob_counts:
            str_repr += f"|\t+ Snapshot: {datetime.fromtimestamp(snapshot_int).date()} - blobs: {r017_count + r327_count} - paired: {r017_count==r327_count}\n"

        str_repr += f"|-No. Employees: {num_employees}\n"
        str_repr += f"|-No. Snapshots: {num_snapshots}\n"

        str_repr += f"[{'='*50}]"

        return str_repr

    def get_codes_ocurrences_by(self, query: str, 
                             mode: Literal['username', 'fullname']) -> Tuple[List[Any], Any]:
        if mode == 'username':
            results, exact_match = self.indexer_username.get_by(query)
            return results, exact_match
        
        elif mode == 'fullname':
            results, exact_match = self.indexer_names.get_by(query)
            return results, exact_match
        
        else:
            raise NotImplementedError(f"There is not a CharTrie for [{mode}].")
        
    def fetch_all(self, query: str) -> pd.DataFrame:

        search_employee_lock.acquire(True)
        self.cursor.execute(query)

        rows = self.cursor.fetchall()
        search_employee_lock.release()

        column_names = [description[0] for description in self.cursor.description]

        df = pd.DataFrame(rows, columns=column_names)

        def move_columns_to_end(df, columns_to_move, new_order=None):
            if new_order is None:
                new_order = columns_to_move

            for col in columns_to_move:
                if col not in df.columns:
                    raise ValueError(f"La columna '{col}' no existe en el DataFrame.")

            remaining_columns = [col for col in df.columns if col not in columns_to_move]

            new_columns = remaining_columns + new_order

            return df[new_columns]
        
        return process_dataframe(move_columns_to_end(df, ['r017_data', 'r327_data']))

    def get_employees_by(self, query: List[str|int], column='employee_code') -> List[EmployeeCapture]:
        results: List[EmployeeCapture] = []

        for code in query:
            search_employee_lock.acquire(True)
            self.cursor.execute(f'''
            SELECT DISTINCT employee_code, employee_dni, username, names, hire_date FROM R017_327
            WHERE {column}=?;
            ''', (int(code),))

            row = self.cursor.fetchone()
            search_employee_lock.release()

            if row:
                employee_code, employee_dni, username, names, hire_date = row
                employee = EmployeeCapture(employee_code=employee_code,
                                           employee_dni=employee_dni,
                                           username=username, 
                                           names=names, 
                                           hire_date=datetime.fromtimestamp(hire_date))
                results.append(employee)
        return results
            

    def copy_from(self, dir: str) -> None:
        try:
            
            db_path2 = os.path.join(dir, os.path.basename(self.db_path))
            idx_username_path2 = os.path.join(dir, 
                                              os.path.basename(self.indexer_names.idx_path))
            idx_names_path2 = os.path.join(dir, 
                                           os.path.basename(self.indexer_username.idx_path))

            shutil.copyfile(db_path2, self.db_path)
            shutil.copyfile(idx_username_path2, self.indexer_username.idx_path)
            shutil.copyfile(idx_names_path2, self.indexer_names.idx_path)
           
            print(f"All files copied successfully from {dir}.")

        except Exception as e:
            print(f"Error copying files: {e}")
