import PyInstaller.__main__
from shutil import copytree, ignore_patterns, rmtree, move
import os
from pathlib import Path

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
copytree('Libs', 'dist/Libs', ignore=ignore_patterns('*.py', '*.pyc', 'Logs', 'Temp', 'Tests', '__pycache__', 'gapy'))

for app_name in apps:
    src_dir = f'dist/tmp{app_name}/'
    copytree(src_dir, 'dist/', dirs_exist_ok=True)
    rmtree(src_dir)

for ext in ['*.pyd', '*.dll']:
    for f in Path('dist/').glob(ext):
        if f.name.startswith('python'): continue
        move(f, 'dist/Libs/')
