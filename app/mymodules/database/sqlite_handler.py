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
from datetime import datetime
from typing import *
from mymodules.database.indexers import CharTrieIndexer
from mymodules.database.employee_handler import EmployeeCapture
from mymodules.thisconstants.vars import *
import os
import io

def valid_file(a_path: str) -> bool:
    return os.path.exists(a_path)
            

def df_to_blob(df: pd.DataFrame) -> bytes:
    buffer_bytes = io.BytesIO()
    pickle.dump(df, buffer_bytes)

    return buffer_bytes.getvalue()

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
        
        if self.connection is not None:
            self.close()

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

    def get_employee_code_by(self, query: str, 
                             mode: Literal['username', 'names']) -> List[str]:
        if mode == 'username':
            return self.indexer_username.get_by(query)
        
        elif mode == 'names':
            return self.indexer_names.get_by(query)
        
        else:
            raise NotImplementedError(f"There is not a CharTrie for [{mode}].")

    def get_employees_by_codes(self, query: List[str|int]) -> List[EmployeeCapture]:
        results: List[EmployeeCapture] = []

        for code in query:
            self.cursor.execute('''
            SELECT DISTINCT employee_code, username, names, hire_date FROM R017_327
            WHERE employee_code=?;
            ''', (int(code),))

            row = self.cursor.fetchone()

            if row:
                employee_code, username, names, hire_date = row
                employee = EmployeeCapture(employee_code=employee_code,
                                           username=username, 
                                           names=names, 
                                           hire_date=hire_date)
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
           
            print(f"All files copied successfully to {dir}.")

        except Exception as e:
            print(f"Error copying files: {e}")