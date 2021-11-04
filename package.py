import PyInstaller.__main__
from shutil import copytree, copy, ignore_patterns, rmtree, move
import os
from pathlib import Path
import sys

is_64bit = sys.maxsize > 2**32

apps = ['PyAI', 'PyBIN', 'PyDAT', 'PyFNT', 'PyGOT', 'PyGRP', 'PyICE', 'PyLO', 'PyMAP', 'PyMPQ', 'PyPAL', 'PyPCX', 'PySPK', 'PyTBL', 'PyTILE', 'PyTRG']

if os.path.exists('dist'):
    rmtree('dist')

PyInstaller.__main__.run([
    'bundle.spec',
    '--noconfirm',
    '--clean',
    '--log-level=WARN'
])

copytree('Images', 'dist/Images')
copytree('Palettes', 'dist/Palettes')
copytree('Libs', 'dist/Libs', ignore=ignore_patterns('*.py', '*.pyc', 'Logs', 'Temp', 'Tests', '__pycache__', 'gapy', 'SFmpq*'))

# Copy SFmpq depending on target platform
copy('Libs/SFmpq-license.txt', 'dist/Libs')
if sys.platform.startswith('win32'):
    copy('Libs/SFmpq64.dll' if is_64bit else 'Libs/SFmpq.dll', 'dist/Libs')
elif sys.platform.startswith('darwin'):
    copy('Libs/SFmpq.dylib', 'dist/Libs')

# Merge all app directories to parent directory
for app_name in apps:
    src_dir = f'dist/tmp{app_name}/'
    copytree(src_dir, 'dist/', dirs_exist_ok=True)
    rmtree(src_dir)

# Move all DLL-type files to Libs
for ext in ['*.pyd', '*.dll']:
    for f in Path('dist/').glob(ext):
        if f.name.startswith('python'): continue
        move(f, 'dist/Libs/')
