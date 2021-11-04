# -*- mode: python ; coding: utf-8 -*-

import os

def get_icon(name):
    desiredIcon = f'Images/{name}.ico'
    return desiredIcon if os.path.exists(desiredIcon) else 'Images/PyMS.ico'

apps = {
  'PyAI': {}, 
  'PyBIN': {}, 
  'PyDAT': {}, 
  'PyFNT': {}, 
  'PyGOT': {}, 
  'PyGRP': {}, 
  'PyICE': {}, 
  'PyLO': {}, 
  'PyMAP': {}, 
  'PyMPQ': {}, 
  'PyPAL': {}, 
  'PyPCX': {}, 
  'PySPK': {}, 
  'PyTBL': {}, 
  'PyTILE': {}, 
  'PyTRG': {}, 
}

exclude_libs = ['_asyncio', '_decimal', '_hashlib', '_multiprocessing', '_overlapped', '_queue', '_ssl', 'unicodedata']

for name, app in apps.items():
    app['analysis'] = Analysis([f'{name}.pyw'], runtime_hooks=['uselib_hook.py'], excludes=exclude_libs)
    app['analysis'].exclude_system_libraries()

MERGE(*[(app['analysis'], name, name) for name, app in apps.items()])

for name, app in apps.items():
    a = app['analysis']
    
    pyz = PYZ(a.pure, a.zipped_data)
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name=name, upx=True, console=False, icon=get_icon(name))
    COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=True, name=f'tmp{name}')
