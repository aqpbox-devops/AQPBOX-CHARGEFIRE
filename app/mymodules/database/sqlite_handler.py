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

def blob_to_series(blob: bytes) -> pd.Series:
    return pickle.load(io.BytesIO(blob))

def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Asegurarse de que el DataFrame tiene al menos dos columnas
    if len(df.columns) < 2:
        raise ValueError("El DataFrame debe tener al menos dos columnas")

    # Obtener los nombres de las dos últimas columnas
    last_two_columns = df.columns[-2:]

    # Crear un nuevo DataFrame para almacenar los resultados
    result_df = df.drop(columns=last_two_columns).copy()

    for index, row in df.iterrows():
        for col in last_two_columns:
            # Deserializar el BLOB a un DataFrame
            try:
                sub_series = blob_to_series(row[col])
                print('SUB SERIES:', type(sub_series))

                for sub_col, value in sub_series.items():
                    if sub_col in result_df.columns:
                        print(f"Advertencia: La columna '{sub_col}' ya existe en el DataFrame principal. Se sobrescribirá.")
                    result_df.at[index, sub_col] = value
            except Exception as e:
                print(f"Error al procesar el BLOB en la columna {col}, fila {index}: {str(e)}")

    return result_df

def get_last_days_of_months(start_date: datetime, end_date: datetime) -> List[int]:
    last_days = []
    current_date = start_date.replace(day=1)  # Asegurarse de que current_date sea el primer día del mes

    while current_date <= end_date:
        next_month = current_date.month % 12 + 1
        year = current_date.year + (current_date.month // 12)
        last_day = datetime(year, next_month, 1) - timedelta(days=1)

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
                        filters: List[str], period: Tuple[datetime, datetime], daily: bool=False) -> pd.DataFrame:
        
        last_days_of_months = get_last_days_of_months(period[0], period[1])

        frequency_snapshot = f"({int(period[0].timestamp())} >= snapshot_date AND snapshot_date <= {int(period[1].timestamp())})"

        if not daily:
            frequency_snapshot = f"snapshot_date IN ({', '.join(['?'] * len(last_days_of_months))})"

        query = f'''
        WITH {target_employee_ref} AS (
            SELECT *
            FROM R017_327
            WHERE employee_code = ?
            AND {frequency_snapshot}
        )
        SELECT *
        FROM R017_327
        WHERE {'\nAND '.join([filter.format(*([target_employee_ref]*(filter.count('{}')))) for filter in filters])}
        AND {frequency_snapshot}
        GROUP BY employee_code;'''

        #query = "SELECT * FROM R017_327 WHERE employee_code = ?;"

        self.cursor.execute(query, (target_employee_code, *(last_days_of_months*2)))

        rows = self.cursor.fetchall()

        column_names = [description[0] for description in self.cursor.description]

        df = pd.DataFrame(rows, columns=column_names)

        print(df.head(1))

        return process_dataframe(df)

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
