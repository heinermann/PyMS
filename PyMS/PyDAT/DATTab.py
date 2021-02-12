
from ContinueImportDialog import ContinueImportDialog

from ..FileFormats.DAT import WeaponsDAT, UpgradesDAT, TechDAT
from ..FileFormats.DAT import UnitsDAT
from ..FileFormats.TBL import decompile_string

from ..Utilities.utils import BASE_DIR, fit, isstr
from ..Utilities.Notebook import NotebookTab
from ..Utilities.Tooltip import Tooltip
from ..Utilities.DataCache import DATA_CACHE
from ..Utilities.PyMSError import PyMSError
from ..Utilities.ErrorDialog import ErrorDialog

from Tkinter import *
import tkMessageBox

import os, copy

DAT_DATA_REF_FILES = {
	'units.dat': 'Units.txt',
	'weapons.dat': 'Weapons.txt',
	'flingy.dat': 'Flingy.txt',
	'sprites.dat': 'Sprites.txt',
	'images.dat': 'Images.txt',
	'upgrades.dat': 'Upgrades.txt',
	'techdata.dat': 'Techdata.txt',
	'sfxdata.dat': 'Sfxdata.txt',
	'portdata.dat': 'Portdata.txt',
	'mapdata.dat': 'Mapdata.txt',
	'orders.dat': 'Orders.txt',
}

class DATTab(NotebookTab):
	data = None

	def __init__(self, parent, toplevel):
		self.id = 0
		self.toplevel = toplevel
		self.icon = self.toplevel.icon
		self.used_by_references = None
		self.used_by_listbox = None
		self.used_by_data = []
		self.entrycopy = None
		self.edited = False
		self.dattabs = None
		NotebookTab.__init__(self, parent)

	def tip(self, obj, tipname, hint):
		obj.tooltip = Tooltip(obj, '%s:\n' % tipname + fit('  ', self.toplevel.data_context.hints[hint], end=True)[:-1], mouse=True)

	def makeCheckbox(self, frame, var, txt, hint):
		c = Checkbutton(frame, text=txt, variable=var)
		self.tip(c, txt, hint)
		return c

	def get_dat_data(self):
		return None

	def setup_used_by(self, references):
		self.used_by_references = references

		f = LabelFrame(self, text='Used By:')
		listframe = Frame(f, bd=2, relief=SUNKEN)
		scrollbar = Scrollbar(listframe)
		self.used_by_listbox = Listbox(listframe, width=1, activestyle=DOTBOX, height=6, bd=0, highlightthickness=0, yscrollcommand=scrollbar.set, exportselection=0)
		self.used_by_listbox.bind('<Double-Button-1>', self.used_by_jump)
		scrollbar.config(command=self.used_by_listbox.yview)
		scrollbar.pack(side=RIGHT, fill=Y)
		self.used_by_listbox.pack(side=LEFT, fill=BOTH, expand=1)
		listframe.pack(fill=X, padx=2, pady=2)
		f.pack(side=BOTTOM, fill=X, padx=2, pady=2)

	def check_used_by_references(self, lookup_id=None, used_by=None):
		self.used_by_data = []
		if not self.used_by_listbox:
			return
		self.used_by_listbox.delete(0,END)
		if not used_by:
			used_by = self.used_by_references
		if not lookup_id:
			lookup_id = self.id
		for datid,get_refs in used_by:
			dat_data = self.toplevel.data_context.dat_data(datid)
			if not dat_data.dat:
				continue
			for check_entry_id in range(dat_data.entry_count()):
				check_entry = dat_data.dat.get_entry(check_entry_id)
				check_refs = get_refs(check_entry)
				for check_ref in check_refs:
					if check_ref.matches(lookup_id):
						self.used_by_data.append((datid, check_entry_id))
						ref_entry_name = dat_data.entry_name(check_entry_id)
						self.used_by_listbox.insert(END, '%s entry %s, %s field: %s' % (dat_data.dat.FILE_NAME, check_entry_id, check_ref.ref_name, ref_entry_name))
						break

	def used_by_jump(self, *_):
		selections = self.used_by_listbox.curselection()
		if not selections:
			return
		selected = selections[0]
		if selected < len(self.used_by_data):
			datid, entry_id = self.used_by_data[selected]
			self.toplevel.dattabs.display(datid.id)
			self.toplevel.changeid(i=entry_id)

	def jump(self, datid, entry_id_var, o=0):
		entry_id = entry_id_var.get() + o
		if entry_id < self.toplevel.data_context.dat_data(datid).entry_count() - 1:
			self.toplevel.dattabs.display(datid)
			self.toplevel.changeid(i=entry_id)

	def updated_entry_names(self, datids):
		pass

	def updated_entry_counts(self, datids):
		pass

	def deactivate(self):
		self.save_data()

	def load_data(self, id=None):
		if not self.get_dat_data().dat:
			return
		if id != None:
			self.id = id
		entry = self.get_dat_data().dat.get_entry(self.id)
		self.load_entry(entry)
		self.check_used_by_references()

	def load_entry(self, entry):
		pass

	def save_data(self):
		if not self.get_dat_data().dat:
			return
		entry = self.get_dat_data().dat.get_entry(self.id)
		self.save_entry(entry)
		self.check_used_by_references()
		if self.edited:
			self.toplevel.update_status_bar()

	def save_entry(self, entry):
		pass

	def unsaved(self):
		if self == self.toplevel.dattabs.active:
			self.save_data()
		if self.edited:
			file = self.get_dat_data().file_path
			if not file:
				file = self.get_dat_data().dat.FILE_NAME
			save = tkMessageBox.askquestion(parent=self, title='Save Changes?', message="Save changes to '%s'?" % file, default=tkMessageBox.YES, type=tkMessageBox.YESNOCANCEL)
			if save != tkMessageBox.NO:
				if save == tkMessageBox.CANCEL:
					return True
				self.save()

	def popup(self, e):
		self.toplevel.listmenu.entryconfig(1, state=[NORMAL,DISABLED][not self.entrycopy])
		if self.get_dat_data().dat.FILE_NAME == 'units.dat':
			self.toplevel.listmenu.entryconfig(3, state=NORMAL)
			self.toplevel.listmenu.entryconfig(4, state=[NORMAL,DISABLED][not self.dattabs.active.tabcopy])
		else:
			self.toplevel.listmenu.entryconfig(3, state=DISABLED)
			self.toplevel.listmenu.entryconfig(4, state=DISABLED)
		self.toplevel.listmenu.post(e.x_root, e.y_root)

	def copy(self, t):
		if not t:
			self.entrycopy = list(self.get_dat_data().dat.entries[self.id])
		elif self.get_dat_data().dat.FILE_NAME == 'units.dat':
			self.dattabs.active.tabcopy = list(self.get_dat_data().dat.entries[self.id])

	def paste(self, t):
		if not t:
			if self.entrycopy:
				self.get_dat_data().dat.entries[self.id] = list(self.entrycopy)
		elif self.get_dat_data().dat.FILE_NAME == 'units.dat' and self.dattabs.active.tabcopy:
			for v in self.dattabs.active.values.keys():
				self.get_dat_data().dat.set_value(self.id, v, self.dattabs.active.tabcopy[self.get_dat_data().dat.labels.index(v)])
		self.toplevel.tab_activated()

	def reload(self):
		self.get_dat_data().dat.set_entry(self.id, copy.deepcopy(self.get_dat_data().default_dat.get_entry(self.id)))
		self.toplevel.tab_activated()

	def new(self, key=None):
		if not self.unsaved():
			self.get_dat_data().dat.new_file()
			self.id = 0
			self.toplevel.tab_activated()

	def open(self, file, save=True):
		if not save or not self.unsaved():
			self.get_dat_data().load_file(file)
			self.id = 0
			if self.toplevel.dattabs.active == self:
				self.toplevel.tab_activated()

	def iimport(self, key=None, file=None, c=True, parent=None):
		if parent == None:
			parent = self
		if not file:
			file = self.toplevel.data_context.settings.lastpath.txt.select_file('import', self, 'Import TXT', '*.txt', [('Text Files','*.txt'),('All Files','*')])
		if not file:
			return
		entries = copy.deepcopy(self.get_dat_data().dat.entries)
		try:
			ids = self.get_dat_data().dat.interpret(file)
		except PyMSError, e:
			self.get_dat_data().dat.entries = entries
			ErrorDialog(self, e)
			return
		cont = c
		for n,_entry in enumerate(entries):
			if cont != 3 and n in ids:
				if cont != 2:
					x = ContinueImportDialog(parent, self.get_dat_data().dat.FILE_NAME, n)
					cont = x.cont
					if cont in [0,3]:
						self.get_dat_data().dat.entries[n] = entries[n]
			else:
				self.get_dat_data().dat.entries[n] = entries[n]
		return cont

	def save(self, key=None):
		if self.get_dat_data().file_path == None:
			self.saveas()
			return
		try:
			self.get_dat_data().dat.compile(self.get_dat_data().file_path)
		except PyMSError, e:
			ErrorDialog(self, e)
		else:
			self.edited = False
			self.toplevel.update_status_bar()

	def saveas(self, key=None):
		file = self.toplevel.data_context.settings.lastpath.dat.save.select_file(self.get_dat_data().dat.FILE_NAME, self, 'Save %s As' % self.get_dat_data().dat.FILE_NAME, '*.dat', [('StarCraft %s files' % self.get_dat_data().dat.FILE_NAME,'*.dat'),('All Files','*')], save=True)
		if not file:
			return True
		self.get_dat_data().file_path = file
		self.save()
		self.toplevel.update_status_bar()

	def export(self, key=None):
		file = self.toplevel.data_context.settings.lastpath.txt.select_file('export', self, 'Export TXT', '*.txt', [('Text Files','*.txt'),('All Files','*')], save=True)
		if not file:
			return True
		try:
			self.get_dat_data().dat.decompile(file)
		except PyMSError, e:
			ErrorDialog(self, e)
