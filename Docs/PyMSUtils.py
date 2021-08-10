from textwrap import wrap

def fit(label, text):
	r = '%s: ' % label
	s = len(r)
	indent = False
	for l in wrap(text, 80 - s):
		if indent:
			r += ' ' * s
		else:
			indent = True
		r += l
		if len(l) != 80 - s:
			r += '\n'
	return r

class PyMSError(Exception):
	def __init__(self, type, error, line=None, code=None, warnings=[]):
		self.type = type
		self.error = error
		self.line = line
		if self.line != None:
			self.line += 1
		self.code = code
		self.warnings = warnings

	def __repr__(self):
		r = fit('%s Error' % self.type, self.error)
		if self.line:
			r += fit('    Line %s' % self.line, self.code)
		if self.warnings:
			for w in self.warnings:
				r += repr(w)
		return r[:-1]

class PyMSWarning(Exception):
	def __init__(self, type, warning, line=None, code=None, extra=None):
		self.type = type
		self.warning = warning
		self.line = line
		if self.line != None:
			self.line += 1
		self.code = code
		self.extra = extra

	def __repr__(self):
		r = fit('%s Warning' % self.type,self.warning)
		if self.line:
			r += fit('    Line %s' % self.line, self.code)
		return r[:-1]

class PyMSWarnList(Exception):
	def __init__(self, warnings):
		self.warnings = warnings

	def __repr__(self):
		r = ''
		for w in self.warnings:
			r += repr(w)
		return r[:-1]
