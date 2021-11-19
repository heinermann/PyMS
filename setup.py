import os
import sys
import shutil
import glob
from cx_Freeze import setup, Executable

is_64bit = sys.maxsize > 2**32
base = "Win32GUI" if sys.platform == "win32" else None


def get_icon(name):
    desiredIcon = f'Images/{name}.ico'
    return desiredIcon if os.path.exists(desiredIcon) else 'Images/PyMS.ico'


executables = []
for prog in ['PyAI', 'PyBIN', 'PyDAT', 'PyFNT', 'PyGOT', 'PyGRP', 'PyICE', 'PyLO', 'PyMAP', 'PyMPQ', 'PyPAL', 'PyPCX', 'PySPK', 'PyTBL', 'PyTILE', 'PyTRG']:
	executables.append(Executable(
		f"{prog}.pyw",
		icon = get_icon(prog),
		base = base
	))


sfmpq_lib = None
if sys.platform.startswith('win32'):
    sfmpq_lib = 'lib/SFmpq64.dll' if is_64bit else 'lib/SFmpq.dll'
elif sys.platform.startswith('darwin'):
	sfmpq_lib = 'lib/SFmpq.dylib'
else:
	raise Exception('SFmpq not built for this OS')

data = [
	'unitdef.txt',
	(sfmpq_lib, sfmpq_lib),
	('lib/SFmpq-license.txt', 'lib/SFmpq-license.txt'),
	('lib/versions.json', 'lib/versions.json'),
	('lib/Data/', 'lib/Data/'),
	('lib/MPQ/', 'lib/MPQ/'),
	('Images/', 'Images/'),
	('Palettes/', 'Palettes/'),
	('Docs/', 'Docs/')
]

exclude_lib = ['asyncio', 'decimal', 'hashlib', 'multiprocessing', 'overlapped', 'queue', 'ssl', 'unicodedata', '_ssl', 'difflib', 'doctest', 'calendar', 'email', 'unittest', 'packaging', 'xml']

exe_options = {
	"include_msvcr": True,
	"include_files": data,
	"excludes": exclude_lib
}

setup(
	name = "PyMS",
	version = "3.0",
	description = "PyMS is a cross platform BroodWar modding suite written using Python.",
	options = {
		"build_exe": exe_options
	},
	executables = executables
)

# Remove files that ended up in incorrect places, mostly because of string references to load them
def remove_glob(path):
	paths = glob.glob(f"build/**/{path}", recursive=True)
	for f in paths:
		shutil.rmtree(f, ignore_errors=True)
		try:
			os.remove(f)
		except Exception:
			pass

remove_glob("lib/lib/SFmpq*.dll")
remove_glob("lib/lib/SFmpq*.dylib")
remove_glob("lib/lib/SFmpq*.txt")
remove_glob("lib/lib/versions.json")
remove_glob("lib/lib/Tests")
remove_glob("lib/lib/Temp")
remove_glob("lib/lib/MPQ")
remove_glob("lib/lib/Data")
remove_glob("lib/tkinter/test")
remove_glob("Docs/*.txt")
remove_glob("Docs/*.py")
