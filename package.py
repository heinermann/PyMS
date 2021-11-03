import PyInstaller.__main__
from shutil import copytree, ignore_patterns
import os
import shutil

def get_icon(name):
    desiredIcon = f'Images/{name}.ico'
    return desiredIcon if os.path.exists(desiredIcon) else 'Images/PyMS.ico'

def package(name):
    print(f'Packaging {name}...')

    PyInstaller.__main__.run([
        f'{name}.pyw',
        '--onefile',
        '--noconsole',
        '--noconfirm',
        '--clean',
        '--log-level=WARN',
        f'--icon={get_icon(name)}'
    ])

if os.path.exists('dist'):
    shutil.rmtree('dist')

package('PyAI')
package('PyBIN')
package('PyDAT')
package('PyFNT')
package('PyGOT')
package('PyGRP')
package('PyICE')
package('PyLO')
package('PyMAP')
package('PyMPQ')
package('PyPAL')
package('PyPCX')
package('PySPK')
package('PyTBL')
package('PyTILE')
package('PyTRG')

copytree('Images', 'dist/Images')
copytree('Palettes', 'dist/Palettes')
copytree('Libs', 'dist/Libs', ignore=ignore_patterns('*.py', '*.pyc', 'Logs', 'Temp', 'Tests', '__pycache__', 'gapy'))
