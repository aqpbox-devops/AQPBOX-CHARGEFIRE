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
import os
import io

def valid_file(a_path: str) -> bool:
    return os.path.exists(a_path)
            

def df_to_blob(df: pd.DataFrame) -> bytes:
    buffer_bytes = io.BytesIO()
    pickle.dump(df, buffer_bytes)

    return buffer_bytes.getvalue()

def get_last_days_of_months(start_date: datetime, end_date: datetime) -> List[int]:
    last_days = []
    current_date = start_date
    
    while current_date <= end_date:
        last_day = (current_date + pd.offsets.MonthEnd(0)).date()
        last_days.append(int(last_day.timestamp()))
        current_date = last_day + timedelta(days=1)
    
    return last_days

class BANTOTALRecordsSQLiteConnection:
    def __init__(self, dir: str, db_name: str = 'BANTOTAL(R)327-017.sqlite') -> None:
        self.db_path = os.path.join(dir, db_name)
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
                             mode: Literal['username', 'fullname']) -> List[str]:
        if mode == 'username':
            return self.indexer_username.get_by(query)
        
        elif mode == 'fullname':
            return self.indexer_names.get_by(query)
        
        else:
            raise NotImplementedError(f"There is not a CharTrie for [{mode}].")

    def fetch_by_filters(self, target_employee_code: int, target_employee_ref: str, 
                        filters: List[str], period: Tuple[datetime, datetime]) -> pd.DataFrame:
        
        last_days_of_months = get_last_days_of_months(period[0], period[1])

        self.cursor.execute(f'''
        WITH {target_employee_ref} AS (
            SELECT *
            FROM R017_327
            WHERE employee_code = ?
        )
        SELECT *
        FROM R017_327
        WHERE {'\nAND '.join([filter.format(target_employee_ref) for filter in filters])}
        AND snapshot_date IN ({', '.join(['?'] * len(last_days_of_months))})
        GROUP BY employee_code;''', (target_employee_code, *last_days_of_months))

        rows = self.cursor.fetchall()

        column_names = [description[0] for description in self.cursor.description]

        df = pd.DataFrame(rows, columns=column_names)

        if len(df.columns) >= 2:
            for i in range(-2, 0):
                blob_data = df.iloc[:, i]

                df.iloc[:, i] = blob_data.apply(lambda x: pd.read_csv(io.BytesIO(x)) if x is not None else None)

        return df

    def get_employees_by(self, query: List[str|int], column='employee_code') -> List[EmployeeCapture]:
        results: List[EmployeeCapture] = []

        for code in query:
            self.cursor.execute(f'''
            SELECT DISTINCT employee_code, employee_dni, username, names, hire_date FROM R017_327
            WHERE {column}=?;
            ''', (int(code),))

            row = self.cursor.fetchone()

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
