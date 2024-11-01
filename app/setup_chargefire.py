import subprocess
import sys

def build_executable():
    command = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--clean',
        '--name', 'app',  # Change this to your desired executable name
        'app/chargefire.py',      # Path to your main script
        '--add-data=app/mymodules:mymodules',
        '--add-data', 'app/templates:templates',  # Include HTML files
        '--add-data', 'app/static:static',
        '--hidden-import', 'flask',
        '--hidden-import', 'pandas',
        '--hidden-import', 'numpy',
        '--hidden-import', 'openpyxl',
        '--hidden-import', 'pyyaml',
        '--hidden-import', 'sqlite3',
        '--hidden-import', 'shutil',  # Agregado
        '--hidden-import', 'pickle',   # Agregado
        '--hidden-import', 'warnings',
        '--hidden-import', 'flaskwebgui'
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