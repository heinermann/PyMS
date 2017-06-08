from Libs.utils import *
from Libs.setutils import *
from Libs.trace import setup_trace
from Libs import GRP, Tilesets, TBL
from Libs.Tilesets import TILETYPE_GROUP, TILETYPE_MEGA, TILETYPE_MINI

from Tkinter import *
from tkMessageBox import *
import tkFileDialog,tkColorChooser

from thread import start_new_thread
from math import ceil,floor
import optparse, os, webbrowser, sys

VERSION = (1,3)
LONG_VERSION = 'v%s.%s' % VERSION
TILE_CACHE = {}

def tip(o, t, h):
	o.tooltip = Tooltip(o, t + ':\n  ' + h, mouse=True)
PAL = [0]

class MegaEditor(PyMSDialog):
	def __init__(self, parent, id):
		self.tileset = parent.tileset
		self.megatile = [id,0]
		self.gettile = parent.gettile
		self.dosave = False
		PyMSDialog.__init__(self, parent, 'MegaTile Editor [%s]' % id)

	def widgetize(self):
		self.minitile = IntegerVar(0,[0,len(self.tileset.vr4.images)-1],callback=lambda id: self.change(id))
		self.flipped = IntVar()
		self.heightdd = IntVar()
		self.walkable = IntVar()
		self.blockview = IntVar()
		self.ramp = IntVar()

		d = Frame(self)
		self.minitiles = Canvas(d, width=101, height=101, background='#000000')
		self.minitiles.pack(padx=2, pady=2)
		self.minitiles.create_rectangle(0, 0, 0, 0, outline='#FFFFFF', tags='border')
		e = Frame(d)
		Label(e, text='MiniTile:').pack(side=LEFT)
		Entry(e, textvariable=self.minitile, font=couriernew, width=5).pack(side=LEFT, padx=2)
		i = PhotoImage(file=os.path.join(BASE_DIR,'Images','find.gif'))
		b = Button(e, image=i, width=20, height=20, command=self.choose)
		b.image = i
		b.pack(side=LEFT, padx=2)
		e.pack(fill=X)
		e = Frame(d)
		i = PhotoImage(file=os.path.join(BASE_DIR,'Images','edit.gif'))
		b = Button(e, image=i, width=20, height=20, command=self.editor)
		b.image = i
		b.pack(side=RIGHT, padx=2)
		Checkbutton(e, text='Flipped', variable=self.flipped).pack(side=RIGHT, padx=2)
		e.pack(fill=X, pady=3)
		d.pack(side=LEFT)
		d = Frame(self)
		c = Frame(d)
		DropDown(c, self.heightdd, ['Low','Med','High'], width=4).pack(side=LEFT, padx=5)
		c.pack(fill=X)
		for t,v in [('Walkable',self.walkable),('Block View',self.blockview),('Ramp?',self.ramp)]:
			c = Frame(d)
			Checkbutton(c, text=t, variable=v).pack(side=LEFT)
			c.pack(fill=X)
		Button(d, text='Apply to all', width=10, command=lambda i=0: self.applyallminiflags(i)).pack(padx=3)
		Button(d, text='Ok', width=10, command=self.ok).pack(side=BOTTOM, padx=3)
		d.pack(side=LEFT, fill=Y, pady=5)
		self.updateminis()
		self.miniload()
		self.minisel()

	def mark_edited(self):
		self.edited = True

	def editor(self):
		MiniEditor(self, self.minitile)

	def updateminis(self):
		self.minitiles.images = []
		for n,m in enumerate(self.tileset.vx4.graphics[self.megatile[0]]):
			t = 'tile%s' % n
			self.minitiles.delete(t)
			self.minitiles.images.append(self.gettile(m))
			self.minitiles.create_image(15 + 25 * (n % 4), 15 + 25 * (n / 4), image=self.minitiles.images[-1], tags=t)
			self.minitiles.tag_bind(t, '<Button-1>', lambda e,n=n: self.miniload(n))
			self.minitiles.tag_bind(t, '<Double-Button-1>', lambda e,i=2: self.parent.choose(i))

	def minisel(self):
		x,y = 2 + 25 * (self.megatile[1] % 4),2 + 25 * (self.megatile[1] / 4)
		self.minitiles.coords('border', x, y, x + 25, y + 25)

	def miniload(self, n=None):
		if self.dosave:
			self.minisave()
		else:
			self.dosave = True
		if n == None:
			n = self.megatile[1]
		else:
			self.megatile[1] = n
		mega = self.megatile[0]
		g = self.tileset.vx4.graphics[mega][n]
		if self.minitile.get() != g[0]:
			self.minitile.check = False
			self.minitile.set(g[0])
		self.flipped.set(g[1])
		f = self.tileset.vf4.flags[mega][n]
		if f & 4:
			self.heightdd.set(2)
		elif f & 2:
			self.heightdd.set(1)
		else:
			self.heightdd.set(0)
		self.walkable.set(f & 1)
		self.blockview.set(f & 8 == 8)
		self.ramp.set(f & 16 == 16)
		self.minisel()

	def minisave(self):
		mega = self.megatile[0]
		self.tileset.vx4.graphics[mega][self.megatile[1]][1] = self.flipped.get()
		self.tileset.vf4.flags[mega][self.megatile[1]] = [0,2,4][self.heightdd.get()] + self.walkable.get() + 8 * self.blockview.get() + 16 * self.ramp.get()

	def change(self, id):
		self.tileset.vx4.graphics[self.megatile[0]][self.megatile[1]][0] = id
		self.updateminis()

	def choose(self):
		TilePalette(self, 2, self.tileset.vx4.graphics[self.megatile[0]][self.megatile[1]][0])

	def ok(self):
		self.minisave()
		del TILE_CACHE[self.megatile[0]]
		try:
			self.parent.megaload()
		except:
			self.parent.draw_tiles()
		PyMSDialog.ok(self)

class Placeability(PyMSDialog):
	def __init__(self, parent, id=0):
		self.id = id
		self.canvass = []
		self.groups = []
		self.tileset = parent.tileset
		self.gettile = parent.gettile
		self.selecting = None
		self.width = 0
		PyMSDialog.__init__(self, parent, 'Doodad Placeability [%s]' % id, resizable=(False,False))

	def widgetize(self):
		f = Frame(self)
		ty = -1
		for n,g in enumerate(self.tileset.cv5.groups[1024:]):
			if g[9] == self.id and ty == -1:
				self.width,h,ty = g[10],g[11],g[11]-1
				if n + h > len(self.tileset.cv5.groups):
					h = len(self.tileset.cv5.groups) - n - 1
					ty = h-1
				for y in range(h):
					self.groups.append([])
					self.canvass.append(Canvas(f, width=self.width * 33-1, height=32))
					self.canvass[-1].grid(sticky=E+W, column=0, row=y*2, columnspan=self.width)
					self.canvass[-1].images = []
					for x in range(self.width):
						c = self.tileset.dddata.doodads[self.id][x + y * self.width]
						if not y:
							t = 'tile%s,%s' % (x,y)
							self.canvass[-1].images.append(Tilesets.megatile_to_photo(self.tileset, g[13][x]))
							self.canvass[-1].create_image(x * 33 + 18, 18, image=self.canvass[-1].images[-1], tags=t)
							self.canvass[-1].tag_bind(t, '<Double-Button-1>', lambda e,p=(x,y): self.select(p))
						self.groups[-1].append(IntegerVar(c,[0,len(self.tileset.cv5.groups)]))
						Entry(f, textvariable=self.groups[-1][-1], width=1, font=couriernew, bd=0).grid(sticky=E+W, column=x, row=y*2+1, padx=x%2)
			elif ty > 0:
				for x in range(self.width):
					c = self.tileset.dddata.doodads[self.id][x + (h-ty) * self.width]
					self.canvass[h-ty].images.append(Tilesets.megatile_to_photo(self.tileset, g[13][x]))
					self.canvass[h-ty].create_image(x * 33 + 18, 18, image=self.canvass[h-ty].images[-1])
					self.canvass[h-ty].tag_bind(t, '<Double-Button-1>', lambda e,p=(x,h-ty): self.select(p))
				ty -= 1
				if not ty:
					break
		f.pack(padx=5,pady=5)

	def select(self, p):
		self.selecting = p
		TilePalette(self, 0, self.groups[p[1]][p[0]].get())

	def change(self, t, id):
		self.groups[self.selecting[1]][self.selecting[0]].set(id)
		self.selecting = None

	def cancel(self, e=None):
		self.ok(self)

	def ok(self, e=None):
		edited = False
		for y,l in enumerate(self.groups):
			for x,g in enumerate(l):
				n = x + y * self.width
				value = g.get()
				old_value = self.tileset.dddata.doodads[self.id][n]
				if value != old_value:
					self.tileset.dddata.doodads[self.id][n] = value
					edited = True
		if edited:
			self.parent.mark_edited()
		PyMSDialog.ok(self)

class MiniEditor(PyMSDialog):
	def __init__(self, parent, id, colors=[0,0]):
		self.colors = colors
		self.click = None
		self.select = False
		self.id = id
		self.edited = True
		PyMSDialog.__init__(self, parent, 'MiniTile Editor [%s]' % id, resizable=(False,False))

	def widgetize(self):
		self.canvas = Canvas(self, width=202, height=114)
		self.canvas.pack(padx=3,pady=3)
		self.canvas.bind('<ButtonRelease-1>', self.release)
		self.canvas.bind('<ButtonRelease-2>', self.release)
		self.canvas.bind('<ButtonRelease-3>', self.release)
		self.canvas.bind('<Motion>', self.motion)
		self.canvas.bind('<B1-Motion>', self.motion)
		self.canvas.bind('<B2-Motion>', self.motion)
		self.canvas.bind('<B3-Motion>', self.motion)
		d = self.parent.tileset.vr4.images[self.id]
		self.colors[0] = d[0][0]
		self.indexs = []
		for y,p in enumerate(d):
			self.indexs.append(list(p))
			for x,i in enumerate(p):
				cx,cy,c = x * 10 + 2, y * 10 + 2, '#%02x%02x%02x' % tuple(self.parent.tileset.wpe.palette[i])
				t = 'tile%s,%s' % (x,y)
				self.canvas.create_rectangle(cx, cy, cx+10, cy+10, fill=c, outline=c, tags=t)
				self.canvas.tag_bind(t, '<Button-1>', lambda e,p=(x,y),c=0: self.color(p,c))
				self.canvas.tag_bind(t, '<Button-2>', lambda e,p=(x,y),c=1: self.color(p,c))
				self.canvas.tag_bind(t, '<Button-3>', lambda e,p=(x,y),c=1: self.color(p,c))
				cx,cy = x + 32,y + 90
				self.canvas.create_rectangle(cx, cy, cx+2, cy+2, fill=c, outline=c, tags='scale%s,%s' % (x,y))
		self.canvas.create_rectangle(90, 2, 202, 114, fill='#000000', outline='#000000')
		for n,i in enumerate(self.parent.tileset.wpe.palette):
			cx,cy,c = (n % 16) * 7 + 91, (n / 16) * 7 + 3, '#%02x%02x%02x' % tuple(i)
			t = 'pal%s' % n
			self.canvas.create_rectangle(cx, cy, cx+5, cy+5, fill=c, outline=c, tags=t)
			c = '#%02x%02x%02x' % tuple(self.parent.tileset.wpe.palette[self.colors[1]])
			self.canvas.tag_bind(t, '<Button-1>', lambda e,p=n,c=0: self.pencolor(p,c))
			self.canvas.tag_bind(t, '<Button-2>', lambda e,p=n,c=1: self.pencolor(p,c))
			self.canvas.tag_bind(t, '<Button-3>', lambda e,p=n,c=1: self.pencolor(p,c))
		c = '#%02x%02x%02x' % tuple(self.parent.tileset.wpe.palette[self.colors[1]])
		self.canvas.create_rectangle(10, 98, 26, 114, fill=c, outline=c, tags='bg')
		c = '#%02x%02x%02x' % tuple(self.parent.tileset.wpe.palette[self.colors[0]])
		self.canvas.create_rectangle(2, 90, 18, 106, fill=c, outline=c, tags='fg')
		self.eyedropper = PhotoImage(file=os.path.join(BASE_DIR,'Images','eyedropper.gif'))
		self.canvas.create_image(56, 101, image=self.eyedropper, tags='eyedropper')
		self.canvas.tag_bind('eyedropper', '<Button-1>', self.dropper)
		b = Frame(self)
		ok = Button(b, text='Ok', width=10, command=self.ok)
		ok.pack(side=LEFT, padx=2)
		Button(b, text='Cancel', width=10, command=self.cancel).pack(side=LEFT)
		b.pack(pady=3)
		return ok

	def dropper(self, e=None):
		if self.select:
			self.canvas.delete('dropbd')
		else:
			self.canvas.create_rectangle(45, 90, 66, 111, outline='#000000', tags='dropbd')
		self.select = not self.select

	def release(self, e):
		self.click = None

	def motion(self, e):
		o = self.canvas.find_overlapping(e.x,e.y,e.x,e.y)
		if self.click != None and o and len(o) == 1:
			t = self.canvas.gettags(o[0])
			if t and len(t) == 1 and t[0].startswith('tile'):
				self.color(tuple(int(n) for n in t[0][4:].split(',')),self.click)

	def color(self, p, c):
		if self.select:
			self.colors[c] = self.indexs[p[1]][p[0]]
			r = '#%02x%02x%02x' % tuple(self.parent.tileset.wpe.palette[self.colors[c]])
			self.canvas.itemconfig(['fg','bg'][c], fill=r, outline=r)
			self.dropper()
		else:
			self.indexs[p[1]][p[0]] = self.colors[c]
			r = '#%02x%02x%02x' % tuple(self.parent.tileset.wpe.palette[self.colors[c]])
			self.canvas.itemconfig('tile%s,%s' % p, fill=r, outline=r)
			self.canvas.itemconfig('scale%s,%s' % p, fill=r, outline=r)
			self.click = c
		self.edited = True

	def pencolor(self, p, c):
		self.colors[c] = p
		r = '#%02x%02x%02x' % tuple(self.parent.tileset.wpe.palette[p])
		self.canvas.itemconfig(['fg','bg'][c], fill=r, outline=r)

	def cancel(self):
		PyMSDialog.cancel(self)

	def ok(self):
		self.parent.tileset.vr4.set_image(self.id, self.indexs)
		self.parent.mark_edited()
		if isinstance(self.parent, PyTILE):
			self.parent.megaload()
		elif isinstance(self.parent, TilePalette):
			TILE_CACHE.clear()
			self.parent.draw_tiles(force=True)
		PyMSDialog.ok(self)

class TilePalette(PyMSDialog):
	def __init__(self, parent, tiletype=TILETYPE_GROUP, select=None):
		PAL[0] += 1
		self.tiletype = tiletype
		self.selected = []
		if select != None:
			self.selected.append(select)
		self.visible_range = None
		self.tileset = parent.tileset
		self.gettile = parent.gettile
		self.select_file = parent.select_file
		self.edited = False
		PyMSDialog.__init__(self, parent, self.get_title(), resizable=(tiletype != TILETYPE_GROUP,True))

	def widgetize(self):
		typename = ''
		if self.tiletype == TILETYPE_GROUP:
			typename = 'Groups'
		elif self.tiletype == TILETYPE_MEGA:
			typename = 'MegaTiles'
		elif self.tiletype == TILETYPE_MINI:
			typename = 'MiniTiles'
		buttons = [
			('add', self.add, 'Add (Insert)', NORMAL, 'Insert'),
			10,
			('export', self.export, 'Export %s (Ctrl+E)' % typename, NORMAL, 'Ctrl+E'),
			('import', self.iimport, 'Import %s (Ctrl+I)' % typename, NORMAL, 'Ctrl+I'),
			20,
			'WIP:',
			('import', self.new_iimport, 'Import %s [WIP]' % typename, NORMAL, None),
		]
		if self.tiletype != TILETYPE_GROUP:
			buttons.extend([10,('edit', self.edit, 'Edit %s (Enter)' % typename, NORMAL, 'Return')])
		self.buttons = {}
		toolbar = Frame(self)
		for btn in buttons:
			if isinstance(btn, tuple):
				image = PhotoImage(file=os.path.join(BASE_DIR,'Images','%s.gif' % btn[0]))
				button = Button(toolbar, image=image, width=20, height=20, command=btn[1], state=btn[3])
				button.image = image
				button.tooltip = Tooltip(button, btn[2])
				button.pack(side=LEFT)
				self.buttons[btn[0]] = button
				a = btn[4]
				if a:
					if not a.startswith('F'):
						self.bind('<%s%s>' % (a[:-1].replace('Ctrl','Control').replace('+','-'), a[-1].lower()), btn[1])
					else:
						self.bind('<%s>' % a, btn[1])
			elif isinstance(btn, str): # WIP, remove later
				Label(toolbar, text=btn).pack(side=LEFT)
			else:
				Frame(toolbar, width=btn).pack(side=LEFT)
		toolbar.pack(fill=X)
		tile_size = self.get_tile_size()
		c = Frame(self)
		self.canvas = Canvas(c, width=2 + tile_size[0] * 16, height=2 + tile_size[1] * 8, background='#000000')
		self.canvas.images = {}
		self.canvas.pack(side=LEFT, fill=BOTH, expand=1)
		scrollbar = Scrollbar(c, command=self.canvas.yview)
		scrollbar.pack(side=LEFT, fill=Y)
		c.pack(side=TOP, fill=BOTH, expand=1)

		self.status = StringVar()
		self.update_status()

		statusbar = Frame(self)
		Label(statusbar, textvariable=self.status, bd=1, relief=SUNKEN, anchor=W).pack(side=LEFT, fill=X, expand=1, padx=1)
		statusbar.pack(side=BOTTOM, fill=X)

		def canvas_resized(e):
			self.update_size()
		self.canvas.bind('<Configure>', canvas_resized)
		self.bind('<MouseWheel>', lambda e: self.canvas.yview('scroll', -(e.delta / abs(e.delta)),'units'))
		self.bind('<Down>', lambda e: self.canvas.yview('scroll', 1,'units'))
		self.bind('<Up>', lambda e: self.canvas.yview('scroll', -1,'units'))
		self.bind('<Next>', lambda e: self.canvas.yview('scroll', 1,'page'))
		self.bind('<Prior>', lambda e: self.canvas.yview('scroll', -1,'page'))
		def update_scrollbar(l,h,bar):
			scrollbar.set(l,h)
			self.draw_tiles()
		self.canvas.config(yscrollcommand=lambda l,h,s=scrollbar: update_scrollbar(l,h,s))

		setting = '%s_palette_window' % ['group','mega','mini'][self.tiletype]
		if setting in self.parent.settings:
			loadsize(self, self.parent.settings, setting)

		if len(self.selected):
			self.after(100, self.scroll_to_selection)

	def mark_edited(self):
		self.edited = True

	def get_title(self):
		count = 0
		max_count = 0
		if self.tiletype == TILETYPE_GROUP:
			count = len(self.tileset.cv5.groups)
			max_count = 4095
		elif self.tiletype == TILETYPE_MEGA:
			count = len(self.tileset.vx4.graphics)
			max_count = 65535
		elif self.tiletype == TILETYPE_MINI:
			count = len(self.tileset.vr4.images)
			max_count = 32767
		return '%s Palette [%d/%d]' % (['Group','MegaTile','MiniTile Image'][self.tiletype], count,max_count)
	def update_title(self):
		self.title(self.get_title())

	def update_status(self):
		status = 'Selected: '
		if len(self.selected):
			for id in self.selected:
				status += '%s ' % id
		else:
			status += 'None'
		self.status.set(status)

	def select(self, select, toggle=False):
		if toggle:
			if select in self.selected:
				self.selected.remove(select)
			else:
				self.selected.append(select)
				self.selected.sort()
		elif isinstance(select, list):
			self.selected = sorted(select)
		else:
			self.selected = [select]
		self.update_status()
		self.draw_selections()
	
	def get_tile_size(self, group=False):
		if self.tiletype == TILETYPE_GROUP:
			return [32.0 * (16 if group else 1),33.0]
		elif self.tiletype == TILETYPE_MEGA:
			return [33.0,33.0]
		elif self.tiletype == TILETYPE_MINI:
			return [25.0,25.0]
	def get_tile_count(self):
		if self.tiletype == TILETYPE_GROUP:
			return len(self.tileset.cv5.groups) * 16
		elif self.tiletype == TILETYPE_MEGA:
			return len(self.tileset.vx4.graphics)
		elif self.tiletype == TILETYPE_MINI:
			return len(self.tileset.vr4.images)
	def get_total_size(self):
		tile_size = self.get_tile_size()
		tile_count = self.get_tile_count()
		width = self.canvas.winfo_width()
		columns = floor(width / tile_size[0])
		total_size = [0,0]
		if columns:
			total_size = [width,int(ceil(tile_count / columns)) * tile_size[1] + 1]
		return total_size

	def update_size(self):
		total_size = self.get_total_size()
		self.canvas.config(scrollregion=(0,0,total_size[0],total_size[1]))
		self.draw_tiles()

	def draw_selections(self):
		self.canvas.delete('selection')
		tile_size = self.get_tile_size(group=True)
		tile_count = self.get_tile_count()
		columns = int(floor(self.canvas.winfo_width() / tile_size[0]))
		if columns:
			for id in self.selected:
				x = (id % columns) * tile_size[0]
				y = (id / columns) * tile_size[1]
				self.canvas.create_rectangle(x, y, x+tile_size[0], y+tile_size[1], outline='#FFFFFF', tags='selection')

	def draw_tiles(self, force=False):
		if force:
			self.visible_range = None
			self.canvas.delete(ALL)
		viewport_size = [self.canvas.winfo_width(),self.canvas.winfo_height()]
		tile_size = self.get_tile_size()
		tile_count = self.get_tile_count()
		total_height = float((self.canvas.cget('scrollregion') or '0').split(' ')[-1])
		topy = int(self.canvas.yview()[0] * total_height)
		start_row = int(floor(topy / tile_size[1]))
		start_y = start_row * int(tile_size[1])
		tiles_size = [int(floor(viewport_size[0] / tile_size[0])),int(ceil((viewport_size[1] + topy-start_y) / tile_size[1]))]
		first = start_row * tiles_size[0]
		last = min(tile_count,first + tiles_size[0] * tiles_size[1]) - 1
		visible_range = [first,last]
		if visible_range != self.visible_range:
			update_ranges = [visible_range]
			overlaps = self.visible_range \
				and ((self.visible_range[0] <= visible_range[0] <= self.visible_range[1] or self.visible_range[0] <= visible_range[1] <= self.visible_range[1]) \
				or (visible_range[0] <= self.visible_range[0] <= visible_range[1] or visible_range[0] <= self.visible_range[1] <= visible_range[1]))
			if overlaps:
				update_ranges = [[min(self.visible_range[0],visible_range[0]),max(self.visible_range[1],visible_range[1])]]
			elif self.visible_range:
				update_ranges.append(self.visible_range)
			for update_range in update_ranges:
				for id in range(update_range[0],update_range[1]+1):
					if (id < visible_range[0] or id > visible_range[1]) and id >= self.visible_range[0] and id <= self.visible_range[1]:
						del self.canvas.images[id]
						self.canvas.delete('tile%s' % id)
					else:
						n = id - visible_range[0]
						x = 1 + (n % tiles_size[0]) * tile_size[0]
						y = 1 + start_y + floor(n / tiles_size[0]) * tile_size[1]
						if self.visible_range and id >= self.visible_range[0] and id <= self.visible_range[1]:
							self.canvas.coords('tile%s' % id, x,y)
						else:
							if self.tiletype == TILETYPE_GROUP:
								group = int(id / 16.0)
								megatile = self.tileset.cv5.groups[group][13][id % 16]
								self.canvas.images[id] = self.gettile(megatile,cache=True)
							elif self.tiletype == TILETYPE_MEGA:
								self.canvas.images[id] = self.gettile(id,cache=True)
							elif self.tiletype == TILETYPE_MINI:
								self.canvas.images[id] = self.gettile((id,0),cache=True)
							tag = 'tile%s' % id
							self.canvas.create_image(x,y, image=self.canvas.images[id], tags=tag, anchor=NW)
							self.canvas.tag_bind(tag, '<Button-1>', lambda e,id=id / (16 if self.tiletype == TILETYPE_GROUP else 1): self.select(id))
							self.canvas.tag_bind(tag, '<Shift-Button-1>', lambda e,id=id / (16 if self.tiletype == TILETYPE_GROUP else 1): self.select(id,True))
							self.canvas.tag_bind(tag, '<Double-Button-1>', lambda e,id=id / (16 if self.tiletype == TILETYPE_GROUP else 1): self.choose(id))
			self.visible_range = visible_range
			self.draw_selections()

	def add(self):
		select = 0
		if self.tiletype == TILETYPE_GROUP:
			self.tileset.cv5.groups.append([0] * 13 + [[0] * 16])
			select = len(self.tileset.cv5.groups)-1
		elif self.tiletype == TILETYPE_MEGA:
			self.tileset.vf4.flags.append([0]*32)
			self.tileset.vx4.graphics.append([[0,0] for _ in range(16)])
			select = len(self.tileset.vx4.graphics)-1
		else:
			self.tileset.vr4.images.append([[0] * 8 for _ in range(8)] )
			select = len(self.tileset.vr4.images)-1
		self.update_title()
		self.update_size()
		self.select(select)
		self.scroll_to_selection()
		self.parent.update_ranges()
		self.mark_edited()

	def export(self):
		if not len(self.selected):
			return
		id = self.selected[0]
		b = self.select_file('Export Group', False, '.bmp', [('256 Color BMP','*.bmp'),('All Files','*')], self, 'lastpath_exports')
		if not b:
			return
		s = None
		if self.tiletype < 2:
			s = self.select_file('Export Group Settings (Cancel to export only the BMP)', False, '.txt', [('Text File','*.txt'),('All Files','*')], self, 'lastpath_exports')
		self.tileset.decompile(b,self.tiletype,id,s)

	def new_iimport(self):
		b = self.select_file('Import Group', True, '.bmp', [('256 Color BMP','*.bmp'),('All Files','*')], self, 'lastpath_exports')
		if not b:
			return
		try:
			new_ids = self.tileset.iimport(self.tiletype, b, self.selected)
		except PyMSError, e:
			ErrorDialog(self, e)
		else:
			TILE_CACHE.clear()
			self.update_title()
			self.update_size()
			if len(new_ids):
				self.select(new_ids)
				self.draw_selections()
				self.scroll_to_selection()
			self.draw_tiles(force=True)
			self.parent.update_ranges()
			self.mark_edited()

	def iimport(self):
		b = self.select_file('Import Group', True, '.bmp', [('256 Color BMP','*.bmp'),('All Files','*')], self, 'lastpath_exports')
		if not b:
			return
		s = None
		if self.tiletype < TILETYPE_MINI:
			s = self.select_file('Import Group Settings (Cancel to import only the BMP)', True, '.txt', [('Text File','*.txt'),('All Files','*')], self, 'lastpath_exports')
		if self.tiletype == TILETYPE_GROUP:
			start_size = len(self.parent.tileset.cv5.groups)
		elif self.tiletype == TILETYPE_MEGA:
			start_size = len(self.parent.tileset.vf4.flags)
		else:
			start_size = len(self.parent.tileset.vr4.images)
		try:
			self.tileset.interpret(b,self.tiletype,s)
		except PyMSError, e:
			ErrorDialog(self, e)
		else:
			if self.tiletype == TILETYPE_GROUP:
				end_size = len(self.parent.tileset.cv5.groups)
			elif self.tiletype == TILETYPE_MEGA:
				end_size = len(self.parent.tileset.vf4.flags)
			else:
				end_size = len(self.parent.tileset.vr4.images)
			if end_size > start_size:
				self.update_title()
				self.update_size()
				select = list(range(start_size,end_size))
				self.select(select)
				self.draw_selections()
				self.scroll_to_selection()
			self.draw_tiles()
			self.parent.update_ranges()
			self.mark_edited()

	def edit(self, e=None):
		if not len(self.selected):
			return
		if self.tiletype == TILETYPE_MEGA:
			MegaEditor(self, self.selected[0])
		elif self.tiletype == TILETYPE_MINI:
			MiniEditor(self, self.selected[0])

	def scroll_to_selection(self):
		if not len(self.selected):
			return
		tile_size = self.get_tile_size(group=True)
		tile_count = self.get_tile_count()
		viewport_size = [self.canvas.winfo_width(),self.canvas.winfo_height()]
		columns = int(floor(viewport_size[0] / tile_size[0]))
		if not columns:
			return
		total_size = self.get_total_size()
		max_y = total_size[1] - viewport_size[1]
		id = self.selected[0]
		y = max(0,min(max_y,(id / columns + 0.5) * tile_size[1] - viewport_size[1]/2.0))
		self.canvas.yview_moveto(y / total_size[1])

	def choose(self, id):
		self.parent.change(self.tiletype, id)
		self.ok()

	def ok(self):
		setting = '%s_palette_window' % ['group','mega','mini'][self.tiletype]
		savesize(self, self.parent.settings, setting)
		if hasattr(self.parent,'selecting'):
			self.parent.selecting = None
		else:
			self.parent.megaload()
			if self.edited:
				self.parent.mark_edited()
		PAL[0] -= 1
		if not PAL[0]:
			TILE_CACHE.clear()
		PyMSDialog.ok(self)

	def cancel(self):
		self.ok()

class PyTILE(Tk):
	def __init__(self, guifile=None):
		self.settings = loadsettings('PyTILE')

		#Window
		Tk.__init__(self)
		self.title('PyTILE %s' % LONG_VERSION)
		try:
			self.icon = os.path.join(BASE_DIR,'Images','PyTILE.ico')
			self.wm_iconbitmap(self.icon)
		except:
			self.icon = '@%s' % os.path.join(BASE_DIR, 'Images','PyTILE.xbm')
			self.wm_iconbitmap(self.icon)
		self.protocol('WM_DELETE_WINDOW', self.exit)
		setup_trace(self, 'PyTILE')
		self.resizable(False, False)

		self.stat_txt = TBL.TBL()
		self.stat_txt_file = ''
		filen = self.settings.get('stat_txt',os.path.join(BASE_DIR, 'Libs', 'MPQ', 'rez', 'stat_txt.tbl'))
		while True:
			try:
				self.stat_txt.load_file(filen)
				break
			except:
				filen = self.select_file('Open stat_txt.tbl', True, '.tbl', [('StarCraft TBL files','*.tbl'),('All Files','*')])
				if not filen:
					sys.exit()

		self.loading_megas = False
		self.loading_minis = False
		self.tileset = None
		self.file = None
		self.edited = False
		self.group = [0,0]
		self.megatile = None

		#Toolbar
		buttons = [
			('open', self.open, 'Open (Ctrl+O)', NORMAL, 'Ctrl+O'),
			('save', self.save, 'Save (Ctrl+S)', DISABLED, 'Ctrl+S'),
			('saveas', self.saveas, 'Save As (Ctrl+Alt+A)', DISABLED, 'Ctrl+Alt+A'),
			('close', self.close, 'Close (Ctrl+W)', DISABLED, 'Ctrl+W'),
			10,
			('register', self.register, 'Set as default *.cv5 editor (Windows Only)', [DISABLED,NORMAL][win_reg], ''),
			('help', self.help, 'Help (F1)', NORMAL, 'F1'),
			('about', self.about, 'About PyTILE', NORMAL, ''),
			10,
			('exit', self.exit, 'Exit (Alt+F4)', NORMAL, 'Alt+F4'),
		]
		self.buttons = {}
		toolbar = Frame(self)
		for btn in buttons:
			if isinstance(btn, tuple):
				image = PhotoImage(file=os.path.join(BASE_DIR,'Images','%s.gif' % btn[0]))
				button = Button(toolbar, image=image, width=20, height=20, command=btn[1], state=btn[3])
				button.image = image
				button.tooltip = Tooltip(button, btn[2])
				button.pack(side=LEFT)
				self.buttons[btn[0]] = button
				a = btn[4]
				if a:
					if not a.startswith('F'):
						self.bind('<%s%s>' % (a[:-1].replace('Ctrl','Control').replace('+','-'), a[-1].lower()), btn[1])
					else:
						self.bind('<%s>' % a, btn[1])
			else:
				Frame(toolbar, width=btn).pack(side=LEFT)
		toolbar.pack(side=TOP, padx=1, pady=1, fill=X)

		self.disable = []
		self.minitile = IntegerVar(0,[0,32767],callback=lambda id: self.change(TILETYPE_MINI, id))
		self.flipped = IntVar()
		self.heightdd = IntVar()
		self.walkable = IntVar()
		self.blockview = IntVar()
		self.ramp = IntVar()

		self.flipped.trace('w', self.minitile_flipped_changed)
		minitile_flag_vars = [self.heightdd,self.walkable,self.blockview,self.ramp]
		for var in minitile_flag_vars:
			var.trace('w', self.minitile_flags_changed)

		self.megatilee = IntegerVar(0,[0,4095],callback=lambda id: self.change(TILETYPE_MEGA, id))
		self.index = IntegerVar(0,[0,65535],callback=self.group_values_changed)
		self.flags = IntegerVar(0,[0,15],callback=self.group_values_changed)
		self.groundheight = IntegerVar(0,[0,15],callback=self.group_values_changed)
		self.buildable = IntegerVar(0,[0,15],callback=self.group_values_changed)
		self.buildable2 = IntegerVar(0,[0,15],callback=self.group_values_changed)
		self.edgeleft = IntegerVar(0,[0,65535],callback=self.group_values_changed)
		self.edgeright = IntegerVar(0,[0,65535],callback=self.group_values_changed)
		self.edgeup = IntegerVar(0,[0,65535],callback=self.group_values_changed)
		self.edgedown = IntegerVar(0,[0,65535],callback=self.group_values_changed)
		self.hasup = IntegerVar(0,[0,65535],callback=self.group_values_changed)
		self.hasdown = IntegerVar(0,[0,65535],callback=self.group_values_changed)
		self.unknown9 = IntegerVar(0,[0,65535],callback=self.group_values_changed)
		self.unknown11 = IntegerVar(0,[0,65535],callback=self.group_values_changed)
		self.doodad = False

		self.findimage = PhotoImage(file=os.path.join(BASE_DIR,'Images','find.gif'))

		self.groupid = LabelFrame(self, text='MegaTile Group')
		g = Frame(self.groupid)
		c = Frame(g)
		self.megatiles = Canvas(c, width=529, height=34, background='#000000')
		self.megatiles.pack()
		self.scroll = Scrollbar(c, orient=HORIZONTAL, command=self.scrolling)
		self.scroll.set(0,1)
		self.scroll.pack(fill=X, expand=1, padx=2)
		c.pack(side=LEFT,padx=2)
		self.megatiles.create_rectangle(0, 0, 0, 0, outline='#FFFFFF', tags='border')
		self.disable.append(Button(g, image=self.findimage, width=20, height=20, command=lambda i=0: self.choose(i), state=DISABLED))
		self.disable[-1].pack(side=LEFT, padx=2)
		g.pack(padx=5)
		f = Frame(self.groupid)
		left = Frame(f)
		l = LabelFrame(left, text='MiniTiles')
		d = Frame(l)
		self.minitiles = Canvas(d, width=101, height=101, background='#000000')
		self.minitiles.pack(padx=2, pady=2)
		self.minitiles.create_rectangle(0, 0, 0, 0, outline='#FFFFFF', tags='border')
		e = Frame(d)
		Label(e, text='MiniTile:').pack(side=LEFT)
		self.disable.append(Entry(e, textvariable=self.minitile, font=couriernew, width=5, state=DISABLED))
		self.disable[-1].pack(side=LEFT, padx=2)
		self.disable.append(Button(e, image=self.findimage, width=20, height=20, command=lambda i=2: self.choose(i), state=DISABLED))
		self.disable[-1].pack(side=LEFT, padx=2)
		e.pack(fill=X)
		e = Frame(d)
		i = PhotoImage(file=os.path.join(BASE_DIR,'Images','edit.gif'))
		self.disable.append(Button(e, image=i, width=20, height=20, command=self.editor, state=DISABLED))
		self.disable[-1].image = i
		self.disable[-1].pack(side=RIGHT, padx=2)
		self.disable.append(Checkbutton(e, text='Flipped', variable=self.flipped, state=DISABLED))
		self.disable[-1].pack(side=RIGHT, padx=2)
		e.pack(fill=X, pady=3)
		d.pack(side=LEFT)
		d = Frame(l)
		c = Frame(d)
		self.disable.append(DropDown(c, self.heightdd, ['Low','Med','High'], width=4, state=DISABLED))
		self.disable[-1].pack(side=LEFT, padx=5)
		c.pack(fill=X)
		for t,v in [('Walkable',self.walkable),('Block View',self.blockview),('Ramp?',self.ramp)]:
			c = Frame(d)
			self.disable.append(Checkbutton(c, text=t, variable=v, state=DISABLED))
			self.disable[-1].pack(side=LEFT)
			c.pack(fill=X)
		a = LabelFrame(d, text='Apply to all')
		self.disable.append(Button(a, text='MiniTiles', width=10, command=lambda i=0: self.applyallminiflags(i), state=DISABLED))
		self.disable[-1].pack(padx=3, pady=2)
		self.disable.append(Button(a, text='MegaTiles', width=10, command=lambda i=1: self.applyallminiflags(i), state=DISABLED))
		self.disable[-1].pack(padx=3, pady=2)
		a.pack(side=BOTTOM, padx=2, pady=2)
		d.pack(side=LEFT, fill=Y)
		l.pack(padx=5, pady=5)
		left.pack(side=LEFT)
		right = Frame(f)
		self.tiles = Frame(right)
		data = [
			[
				('Index',self.index,5,'Group Index? Seems to always be 1 for doodads. Not completely understood'),
				('MegaTile',self.megatilee,4,'MegaTile ID for selected tile in the group. Either input a value,\n  or hit the find button to browse for a MegaTile.')
			],
			[
				('Flags',self.flags,2,'Unknown property:\n    0 = ?\n    1 = Edge?\n    4 = Cliff?'),
				('Ground Height',self.groundheight,2,'Shows ground height. Does not seem to be completely valid.\n  May be used by StarEdit/deprecated?'),
				('Edge Left?',self.edgeleft,5,'Unknown. Seems to be related to surrounding tiles & ISOM. (Left?)'),
				('Edge Right?',self.edgeright,5,'Unknown. Seems to be related to surrounding tiles & ISOM. (Right?)'),
				('Edge Up?',self.edgeup,5,'Unknown. Seems to be related to surrounding tiles & ISOM. (Up?)'),
				('Edge Down?',self.edgedown,5,'Unknown. Seems to be related to surrounding tiles & ISOM. (Down?)')
			],
			[
				('Buildable',self.buildable,2,'Sets the default buildable property:\n    0 = Buildable\n    4 = Creep\n    8 = Unbuildable'),
				('Buildable 2',self.buildable2,2,'Buildable Flag for Beacons/Start Location:\n    0 = Default\n    8 = Buildable'),
				('Has Up',self.hasup,5,'Edge piece has rows above it. (Recently noticed; not fully understood.)\n    1 = Basic edge piece.\n    2 = Right edge piece.\n    3 = Left edge piece.'),
				('Has Down',self.hasdown,5,'Edge piece has rows below it. (Recently noticed; not fully understood.)\n    1 = Basic edge piece.\n    2 = Right edge piece.\n    3 = Left edge piece.'),
				('Unknown 9',self.unknown9,5,'Unknown'),
				('Unknown 11',self.unknown11,5,'Unknown')
			],
		]
		for c,a in enumerate(data):
			for r,row in enumerate(a):
				t,v,w,desc = row
				l = Label(self.tiles, text=t + ':', anchor=E)
				if t == 'MegaTile':
					l.grid(sticky=W+E, column=c*2, row=5)
					tip(l, t, desc)
					e = Frame(self.tiles)
					self.disable.append(Entry(e, textvariable=v, font=couriernew, width=w, state=DISABLED))
					self.disable[-1].pack(side=LEFT)
					self.disable.append(Button(e, image=self.findimage, width=20, height=20, command=lambda i=1: self.choose(i), state=DISABLED))
					self.disable[-1].pack(side=LEFT, padx=2)
					e.grid(sticky=W, column=c*2+1, row=5)
					tip(e, t, desc)
				else:
					l.grid(sticky=W+E, column=c*2, row=r)
					tip(l, t, desc)
					self.disable.append(Entry(self.tiles, textvariable=v, font=couriernew, width=w, state=DISABLED))
					self.disable[-1].grid(sticky=W, column=c*2+1, row=r)
					tip(self.disable[-1], t, desc)
		self.tiles.pack(side=TOP)
		self.doodads = Frame(right)
		data = [
			[
				('Index',self.index,5,'Group Index? Seems to always be 1 for doodads. Not completely understood'),
				('MegaTile',self.megatilee,4,'MegaTile ID for selected tile in the group. Either input a value,\n  or hit the find button to browse for a MegaTile.')
			],
			[
				('Unknown 1',self.flags,2,'Unknown:\n    0 = ?\n    1 = ?'),
				('Ground Height',self.groundheight,2,'Shows ground height. Does not seem to be completely valid.\n  May be used by StarEdit/deprecated?'),
				(None,self.edgeleft,None,'Doodad group string from stat_txt.tbl'),
				('Doodad #',self.edgeright,5,'Doodad ID used used for dddata.bi'),
				('Doodad Width',self.edgeup,5,'Total width of the doodad in MegaTiles'),
				('Doodad Height',self.edgedown,5,'Total height of the doodad in MegaTiles')
			],
			[
				('Buildable',self.buildable,2,'Sets the default buildable property:\n    0 = Buildable\n    4 = Creep\n    8 = Unbuildable'),
				('Has Overlay',self.buildable2,2,'Flag that determins if a doodad has a sprite overlay:\n    0 = None\n    1 = Sprites.dat Reference\n    2 = Units.dat Reference\n    4 = Overlay is Flipped'),
				('Overlay ID',self.hasup,5,'Sprite or Unit ID (depending on the Has Overlay flag) of the doodad overlay.'),
				('Unknown 6',self.hasdown,5,'Unknown'),
				('Unknown 8',self.unknown9,5,'Unknown'),
				('Unknown 12',self.unknown11,5,'Unknown')
			],
		]
		for c,a in enumerate(data):
			for r,row in enumerate(a):
				t,v,w,desc = row
				if t == None:
					l = Label(self.doodads, text='Group:', anchor=E)
					l.grid(sticky=W+E, column=0, row=2)
					tip(l, 'Doodad Group', desc)
					self.doodaddd = DropDown(self.doodads, v, [TBL.decompile_string(s) for s in self.stat_txt.strings])
					self.doodaddd.grid(sticky=W+E, column=1, row=r, columnspan=3)
				else:
					l = Label(self.doodads, text=t + ':', anchor=E)
					if t == 'MegaTile':
						l.grid(sticky=W+E, column=c*2, row=5)
						tip(l, t, desc)
						e = Frame(self.doodads)
						self.disable.append(Entry(e, textvariable=v, font=couriernew, width=w, state=DISABLED))
						self.disable[-1].pack(side=LEFT)
						self.disable.append(Button(e, image=self.findimage, width=20, height=20, command=lambda i=1: self.choose(i), state=DISABLED))
						self.disable[-1].pack(side=LEFT, padx=2)
						e.grid(sticky=W, column=c*2+1, row=5)
					else:
						l.grid(sticky=W+E, column=c*2, row=r)
						tip(l, t, desc)
						self.disable.append(Entry(self.doodads, textvariable=v, font=couriernew, width=w, state=DISABLED))
						self.disable[-1].grid(sticky=W, column=c*2+1, row=r)
						tip(self.disable[-1], t, desc)
		self.disable.append(Button(self.doodads, text='Placeability', command=self.placeability))
		self.disable[-1].grid(sticky=W+E, column=2, row=7, pady=5)
		right.pack(side=LEFT, fill=Y, pady=8)
		f.pack(fill=X)
		self.groupid.pack(padx=5, pady=5)

		#Statusbar
		self.status = StringVar()
		statusbar = Frame(self)
		Label(statusbar, textvariable=self.status, bd=1, relief=SUNKEN, width=75, anchor=W).pack(side=LEFT, padx=1)
		image = PhotoImage(file=os.path.join(BASE_DIR,'Images','save.gif'))
		self.editstatus = Label(statusbar, image=image, bd=0, state=DISABLED)
		self.editstatus.image = image
		self.editstatus.pack(side=LEFT, padx=1, fill=Y)
		Label(statusbar, bd=1, relief=SUNKEN, anchor=W).pack(side=LEFT, expand=1, padx=1, fill=X)
		self.status.set('Load a Tileset.')
		statusbar.pack(side=BOTTOM, fill=X)

		if 'window' in self.settings:
			loadsize(self, self.settings)

		if guifile:
			self.open(file=guifile)

		start_new_thread(check_update, (self,))

	def unsaved(self):
		if self.tileset and self.edited:
			file = self.file
			if not file:
				file = 'Unnamed.cv5'
			save = askquestion(parent=self, title='Save Changes?', message="Save changes to '%s'?" % file, default=YES, type=YESNOCANCEL)
			if save != 'no':
				if save == 'cancel':
					return True
				if self.file:
					self.save()
				else:
					self.saveas()

	def select_file(self, title, open=True, ext='.cv5', filetypes=[('Complete Tileset','*.cv5'),('All Files','*')], parent=None, setting='lastpath'):
		if parent == None:
			parent = self
		path = self.settings.get(setting, BASE_DIR)
		file = [tkFileDialog.asksaveasfilename,tkFileDialog.askopenfilename][open](title=title, defaultextension=ext, filetypes=filetypes, initialdir=path, parent=parent)
		if file:
			self.settings[setting] = os.path.dirname(file)
		return file

	def action_states(self):
		file = [NORMAL,DISABLED][not self.tileset]
		for btn in ['save','saveas','close']:
			self.buttons[btn]['state'] = file
		for w in self.disable:
			w['state'] = file

	def mark_edited(self, edited=True):
		self.edited = edited
		self.editstatus['state'] = [DISABLED,NORMAL][edited]

	def gettile(self, id, cache=False):
		to_photo = [Tilesets.megatile_to_photo,Tilesets.minitile_to_photo][isinstance(id,tuple) or isinstance(id,list)]
		if cache:
			if not id in TILE_CACHE:
				TILE_CACHE[id] = to_photo(self.tileset, id)
			return TILE_CACHE[id]
		return to_photo(self.tileset, id)

	def applyallminiflags(self, i):
		megas = self.tileset.cv5.groups[self.group[0]][13]
		if i == 0:
			megas = [megas[self.group[1]]]
		for mega in megas:
			for n in range(16):
				self.tileset.vf4.flags[mega][n] = self.heightdd.get() * 2 + self.walkable.get() + 8 * self.blockview.get() + 16 * self.ramp.get()

	def draw_group_selection(self):
		x = 2 + 33 * self.group[1]
		self.megatiles.coords('border', x, 2, x + 33, 35)

	def draw_group(self):
		d = ['',' - Doodad'][self.group[0] >= 1024]
		self.groupid['text'] = 'MegaTile Group [%s%s]' % (self.group[0],d)
		self.megatiles.images = []
		for n,m in enumerate(self.tileset.cv5.groups[self.group[0]][13]):
			t = 'tile%s' % n
			self.megatiles.delete(t)
			self.megatiles.images.append(self.gettile(m))
			self.megatiles.create_image(19 + 33 * n, 19, image=self.megatiles.images[-1], tags=t)
			self.megatiles.tag_bind(t, '<Button-1>', lambda e,n=n: self.megaload(n))
			self.megatiles.tag_bind(t, '<Double-Button-1>', lambda e,i=1: self.choose(i))

	def megaload(self, n=None):
		self.loading_megas = True
		if n == None:
			n = self.group[1]
		else:
			self.group[1] = n
		group = self.tileset.cv5.groups[self.group[0]]
		mega = group[13][n]
		self.megatile[0] = mega
		if self.megatilee.get() != mega:
			self.megatilee.check = False
			self.megatilee.set(mega)
		self.index.set(group[0])
		if self.group[0] >= 1024:
			if not self.doodad:
				self.tiles.pack_forget()
				self.doodads.pack(side=TOP)
				self.doodad = True
			o = [self.buildable,self.flags,self.buildable2,self.groundheight,self.hasup,self.hasdown,self.edgeleft,self.unknown9,self.edgeright,self.edgeup,self.edgedown,self.unknown11]
		else:
			if self.doodad:
				self.doodads.pack_forget()
				self.tiles.pack(side=TOP)
				self.doodad = False
			o = [self.buildable,self.flags,self.buildable2,self.groundheight,self.edgeleft,self.edgeup,self.edgeright,self.edgedown,self.unknown9,self.hasup,self.unknown11,self.hasdown]
		for n,v in enumerate(o):
			if self.group[0] >= 1024 and n == 6:
				v.set(group[n+1]-1)
			else:
				v.set(group[n+1])
		self.draw_group()
		self.draw_group_selection()
		self.miniload()
		self.loading_megas = False

	def draw_minitiles_selection(self):
		x,y = 2 + 25 * (self.megatile[1] % 4),2 + 25 * (self.megatile[1] / 4)
		self.minitiles.coords('border', x, y, x + 25, y + 25)

	def draw_minitiles(self):
		self.minitiles.images = []
		for n,m in enumerate(self.tileset.vx4.graphics[self.megatile[0]]):
			t = 'tile%s' % n
			self.minitiles.delete(t)
			self.minitiles.images.append(self.gettile(m))
			self.minitiles.create_image(15 + 25 * (n % 4), 15 + 25 * (n / 4), image=self.minitiles.images[-1], tags=t)
			self.minitiles.tag_bind(t, '<Button-1>', lambda e,n=n: self.miniload(n))
			self.minitiles.tag_bind(t, '<Double-Button-1>', lambda e,i=2: self.choose(i))

	def miniload(self, n=None):
		self.loading_minis = True
		if n == None:
			n = self.megatile[1]
		else:
			self.megatile[1] = n
		mega = self.tileset.cv5.groups[self.group[0]][13][self.group[1]]
		g = self.tileset.vx4.graphics[mega][n]
		if self.minitile.get() != g[0]:
			self.minitile.check = False
			self.minitile.set(g[0])
		self.flipped.set(g[1])
		f = self.tileset.vf4.flags[mega][n]
		if f & 4:
			self.heightdd.set(2)
		elif f & 2:
			self.heightdd.set(1)
		else:
			self.heightdd.set(0)
		self.walkable.set(f & 1)
		self.blockview.set(f & 8 == 8)
		self.ramp.set(f & 16 == 16)
		self.draw_minitiles()
		self.draw_minitiles_selection()
		self.loading_minis = False


	def group_values_changed(self, *_):
		if not self.tileset or self.loading_megas:
			return
		group = self.tileset.cv5.groups[self.group[0]]
		group[0] = self.index.get()
		if self.group[0] >= 1024:
			o = [self.buildable,self.flags,self.buildable2,self.groundheight,self.hasup,self.hasdown,self.edgeleft,self.unknown9,self.edgeright,self.edgeup,self.edgedown,self.unknown11]
		else:
			o = [self.buildable,self.flags,self.buildable2,self.groundheight,self.edgeleft,self.edgeup,self.edgeright,self.edgedown,self.unknown9,self.hasup,self.unknown11,self.hasdown]
		for n,v in enumerate(o):
			if self.group[0] >= 1024 and n == 6:
				group[n+1] = v.get()+1
			else:
				group[n+1] = v.get()
		self.mark_edited()

	def minitile_flipped_changed(self, *_):
		if not self.tileset or self.loading_minis:
			return
		megatile_id = self.tileset.cv5.groups[self.group[0]][13][self.group[1]]
		minitile_n = self.megatile[1]
		tile = list(self.tileset.vx4.graphics[megatile_id])
		tile[minitile_n] = (tile[minitile_n][0],self.flipped.get())
		self.tileset.vx4.set_tile(megatile_id, tile)
		self.draw_minitiles()
		self.draw_group()
		self.mark_edited()

	def minitile_flags_changed(self, *_):
		if not self.tileset or self.loading_minis:
			return
		flags = [0,2,4][self.heightdd.get()] + self.walkable.get() + 8 * self.blockview.get() + 16 * self.ramp.get()
		megatile_id = self.tileset.cv5.groups[self.group[0]][13][self.group[1]]
		minitile_n = self.megatile[1]
		self.tileset.vf4.flags[megatile_id][minitile_n] = flags
		self.mark_edited()

	def choose(self, i):
		TilePalette(self, i, [
			self.group[0],
			self.tileset.cv5.groups[self.group[0]][13][self.group[1]],
			self.tileset.vx4.graphics[self.tileset.cv5.groups[self.group[0]][13][self.group[1]]][self.megatile[1]][0]
		][i])

	def updatescroll(self):
		groups = 0
		if self.tileset:
			groups = float(len(self.tileset.cv5.groups)-1)
		if groups <= 1:
			self.scroll.set(0,1)
		else:
			x = (1-8/groups)*(self.group[0] / groups)
			self.scroll.set(x,x+(8/groups))

	def scrolling(self, t, p, e=None):
		a = {'page':8,'pages':8,'units':1}
		groups = len(self.tileset.cv5.groups)-1
		p = min(100,float(p) / (1-8/float(groups)))
		if t == 'moveto':
			self.group[0] = int(groups * float(p))
		elif t == 'scroll':
			self.group[0] = min(groups,max(0,self.group[0] + int(p) * a[e]))
		self.updatescroll()
		self.megaload()

	def change(self, tiletype, id):
		if not self.tileset:
			return
		if tiletype == TILETYPE_GROUP:
			self.group[0] = id
			self.megaload()
		elif tiletype == TILETYPE_MEGA and not self.loading_megas:
			self.megatile[0] = id
			self.tileset.cv5.groups[self.group[0]][13][self.group[1]] = id
			self.draw_group()
			self.draw_minitiles()
		elif tiletype == TILETYPE_MINI and not self.loading_minis:
			megatile_id = self.tileset.cv5.groups[self.group[0]][13][self.group[1]]
			tile = self.tileset.vx4.graphics[megatile_id]
			minitile_n = self.megatile[1]
			if tile[minitile_n][0] != id:
				self.megatile[1] = id
				tile = list(tile)
				tile[minitile_n] = (id,tile[minitile_n][1])
				self.tileset.vx4.set_tile(megatile_id, tile)
				self.draw_group()
				self.draw_minitiles()
		self.updatescroll()
		self.mark_edited()

	def placeability(self):
		Placeability(self, self.edgeright.get())

	def editor(self):
		minitile_image_id = self.tileset.vx4.graphics[self.megatile[0]][self.megatile[1]][0]
		MiniEditor(self, minitile_image_id)

	def update_ranges(self):
		self.megatilee.setrange([0,len(self.tileset.vf4.flags)-1])
		self.minitile.setrange([0,len(self.tileset.vr4.images)-1])

	def open(self, key=None, file=None):
		if not self.unsaved():
			if file == None:
				file = self.select_file('Open Complete Tileset')
				if not file:
					return
			tileset = Tilesets.Tileset()
			try:
				tileset.load_file(file)
			except PyMSError, e:
				ErrorDialog(self, e)
				return
			self.tileset = tileset
			self.file = file
			self.status.set('Load successful!')
			self.mark_edited(False)
			self.action_states()
			self.update_ranges()
			self.group = [0,0]
			self.megatile = [self.tileset.cv5.groups[0][13][0],0]
			self.megaload()
			self.updatescroll()

	def save(self, key=None):
		if key and self.buttons['save']['state'] != NORMAL:
			return
		if self.file == None:
			self.saveas()
			return
		try:
			self.tileset.save_file(self.file)
			self.status.set('Save Successful!')
			self.mark_edited(False)
		except PyMSError, e:
			ErrorDialog(self, e)

	def saveas(self, key=None):
		if key and self.buttons['saveas']['state'] != NORMAL:
			return
		file = self.select_file('Save Tileset As', False)
		if not file:
			return True
		self.file = file
		self.save()

	def close(self, key=None):
		if key and self.buttons['close']['state'] != NORMAL:
			return
		if not self.unsaved():
			self.tileset = None
			self.file = None
			self.group = [0,0]
			self.megatile = None
			self.status.set('Load or create a Tileset.')
			self.mark_edited(False)
			self.groupid['text'] = 'MegaTile Group'
			if self.doodad:
				self.doodads.pack_forget()
				self.tiles.pack(side=TOP)
				self.doodad = False
			for v in [self.minitile,self.flipped,self.heightdd,self.walkable,self.blockview,self.ramp,self.index,self.megatilee,self.buildable,self.flags,self.buildable2,self.groundheight,self.edgeleft,self.edgeup,self.edgeright,self.edgedown,self.unknown9,self.hasup,self.unknown11,self.hasdown]:
				v.set(0)
			for n in range(16):
				t = 'tile%s' % n
				self.megatiles.delete(t)
				self.minitiles.delete(t)
			self.megatiles.images = []
			self.minitiles.images = []
			self.megatiles.coords('border', 0, 0, 0, 0)
			self.minitiles.coords('border', 0, 0, 0, 0)
			self.action_states()
			self.updatescroll()

	def register(self, e=None):
		try:
			register_registry('PyTILE','','cv5',os.path.join(BASE_DIR, 'PyTILE.pyw'),os.path.join(BASE_DIR,'Images','PyTILE.ico'))
		except PyMSError, e:
			ErrorDialog(self, e)

	def help(self, e=None):
		webbrowser.open('file:///%s' % os.path.join(BASE_DIR, 'Docs', 'PyTILE.html'))

	def about(self, key=None):
		AboutDialog(self, 'PyTILE', LONG_VERSION, [('FaRTy1billion','Tileset file specs and HawtTiles.')])

	def exit(self, e=None):
		if not self.unsaved():
			savesize(self, self.settings, size=False)
			savesettings('PyTILE', self.settings)
			self.destroy()

def main():
	import sys
	if not sys.argv or (len(sys.argv) == 1 and os.path.basename(sys.argv[0]).lower() in ['','pytile.py','pytile.pyw','pytile.exe']):
		gui = PyTILE()
		gui.mainloop()
	else:
		p = optparse.OptionParser(usage='usage: PyTILE [options]', version='PyTILE %s' % LONG_VERSION)
		# p.add_option('-v', '--vf4', metavar='FILE', help='Choose a palette for GRP to BMP conversion [default: %default]', default='')
		# p.add_option('-p', '--palette', metavar='FILE', help='Choose a palette for GRP to BMP conversion [default: %default]', default='Units.pal')
		# p.add_option('-g', '--grptobmps', action='store_true', dest='convert', help="Converting from GRP to BMP's [default]", default=True)
		# p.add_option('-b', '--bmpstogrp', action='store_false', dest='convert', help="Converting from BMP's to GRP")
		# p.add_option('-u', '--uncompressed', action='store_true', help="Used to signify if the GRP is uncompressed (both to and from BMP) [default: Compressed]", default=False)
		# p.add_option('-o', '--onebmp', action='store_true', help='Used to signify that you want to convert a GRP to one BMP file. [default: Multiple]', default=False)
		# p.add_option('-f', '--frames', type='int', help='Used to signify you are using a single BMP with alll frames, and how many frames there are.', default=0)
		p.add_option('--gui', help="Opens a file with the GUI", default='')
		opt, args = p.parse_args()
		if opt.gui:
			gui = PyTILE(opt.gui)
			gui.mainloop()

if __name__ == '__main__':
	main()