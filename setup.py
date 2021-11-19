import os
import sys
import shutil
import glob
from cx_Freeze import setup, Executable

is_64bit = sys.maxsize > 2**32

# base="Win32GUI" should be used only for Windows GUI app
base = None
if sys.platform == "win32":
    base = "Win32GUI"


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
    sfmpq_lib = 'Libs/SFmpq64.dll' if is_64bit else 'Libs/SFmpq.dll'
elif sys.platform.startswith('darwin'):
	sfmpq_lib = 'Libs/SFmpq.dylib'
else:
	raise Exception('SFmpq not built for this OS')

data = [
	'unitdef.txt',
	(sfmpq_lib, sfmpq_lib),
	('Libs/SFmpq-license.txt', 'Libs/SFmpq-license.txt'),
	('Libs/versions.json', 'Libs/versions.json'),
	('Libs/Data/', 'Libs/Data/'),
	('Libs/MPQ/', 'Libs/MPQ/'),
	('Images/', 'Images/'),
	('Palettes/', 'Palettes/'),
	('Docs/', 'Docs/')
]

exclude_libs = ['asyncio', 'decimal', 'hashlib', 'multiprocessing', 'overlapped', 'queue', 'ssl', 'unicodedata', '_ssl', 'difflib', 'doctest', 'calendar', 'email', 'unittest', 'packaging', 'xml']

exe_options = {
	"include_msvcr": True,
	"include_files": data,
	"excludes": exclude_libs
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

remove_glob("lib/Libs/SFmpq*.dll")
remove_glob("lib/Libs/SFmpq*.dylib")
remove_glob("lib/Libs/SFmpq*.txt")
remove_glob("lib/Libs/versions.json")
remove_glob("lib/Libs/Tests")
remove_glob("lib/Libs/Temp")
remove_glob("lib/Libs/MPQ")
remove_glob("lib/Libs/Data")
remove_glob("lib/tkinter/test")
remove_glob("Docs/*.txt")
remove_glob("Docs/*.py")
