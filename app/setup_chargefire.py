import subprocess
import sys

def build_executable():
    command = [
        'pyinstaller',
        '--onefile',
        '--clean',
        '--name', 'chargefire',  # Change this to your desired executable name
        'app/chargefire.py',      # Path to your main script
        '--add-data', 'app/static;static',  # Include static files if needed
        
        # Include your custom modules as hidden imports
        '--hidden-import', 'mymodules.core.app_chargefire',
        '--hidden-import', 'mymodules.core.appcore',
        '--hidden-import', 'mymodules.core.employee',
        '--hidden-import', 'mymodules.core.excel_builder',
        '--hidden-import', 'mymodules.database.indexers',
        '--hidden-import', 'mymodules.thisconstants.functions',
        '--hidden-import', 'mymodules.thisconstants.vars',

        # Include external libraries as hidden imports
        '--hidden-import', 'flask',
        '--hidden-import', 'pandas',
        '--hidden-import', 'numpy',
        '--hidden-import', 'openpyxl',
        '--hidden-import', 'pyyaml',
        '--hidden-import', 'sqlite3'   # Include SQLite3 as hidden import (standard library)
    ]

    try:
        # Execute the command
        subprocess.run(command, check=True)
        print("Build completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error while compiling: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()