

import __main__
import FreeCADGui as Gui
import FreeCAD as App
from .utils import search_for_expressions

from PySide import QtCore, QtGui

class SearchTab(QtGui.QWidget):

	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		search_layout = QtGui.QFormLayout(self)
		search_layout.setContentsMargins(QtCore.QMargins(0, 5, 0, 5))

		search_term = QtGui.QLineEdit("")
		self.search_term = search_term
		search_layout.addRow("Search for Alias", search_term) # type: ignore
		search_term.textChanged.connect(self.search)

		replace_term = QtGui.QLineEdit("")
		self.replace_term = replace_term
		search_layout.addRow("Replace Alias With", replace_term) # type: ignore
		replace_term.textChanged.connect(self.search)

		# OPTIONS
		search_options_layout = QtGui.QGridLayout(self)
		search_options_layout.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))
		search_layout.addRow(search_options_layout)

		search_globally = QtGui.QCheckBox("Search All Documents")
		self.search_globally = search_globally
		search_options_layout.addWidget(search_globally, 0, 0)  # type: ignore
		search_globally.setChecked(True)
		search_globally.stateChanged.connect(self.search)

		focus_object_on_sel = QtGui.QCheckBox("Focus Object on Selection")
		self.focus_object_on_sel = focus_object_on_sel
		search_options_layout.addWidget(focus_object_on_sel, 1, 0)  # type: ignore
		focus_object_on_sel.setChecked(True)

		include_spreadsheets = QtGui.QCheckBox("Include Spreadsheet Cells")
		include_spreadsheets.setToolTip("Include spreadsheet cells (only regular cells, not expression cells)")
		self.include_spreadsheets = include_spreadsheets
		search_options_layout.addWidget(include_spreadsheets, 0, 1)  # type: ignore
		include_spreadsheets.setChecked(True)
		include_spreadsheets.stateChanged.connect(self.search)

		include_spreadsheet_expressions = QtGui.QCheckBox("Include Spreadsheet Expressions")
		include_spreadsheet_expressions.setToolTip("Include spreadsheet cells with expressions (start with `=`).")
		include_spreadsheet_expressions.setChecked(True)
		self.include_spreadsheet_expressions = include_spreadsheet_expressions
		search_options_layout.addWidget(include_spreadsheet_expressions, 1, 1)  # type: ignore				
		include_spreadsheet_expressions.stateChanged.connect(self.search)	


		include_spreadsheet_aliases = QtGui.QCheckBox("Include Spreadsheet Aliases")
		include_spreadsheet_aliases.setToolTip("Include spreadsheet aliases.")
		include_spreadsheet_aliases.setChecked(True)
		self.include_spreadsheet_aliases = include_spreadsheet_aliases
		search_options_layout.addWidget(include_spreadsheet_aliases, 2, 1)  # type: ignore
		include_spreadsheet_aliases.stateChanged.connect(search_for_expressions)
		

		# BUTTONS
		search_buttons_layout = QtGui.QHBoxLayout(self)
		search_buttons_layout.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))

		check_all_button = QtGui.QPushButton("Check All")
		self.check_all_button =check_all_button
		search_buttons_layout.addWidget(check_all_button)
		check_all_button.clicked.connect(self.check_all)

		uncheck_all_button = QtGui.QPushButton("Uncheck All")
		self.uncheck_all_button = uncheck_all_button
		search_buttons_layout.addWidget(uncheck_all_button)
		uncheck_all_button.clicked.connect(self.uncheck_all)

		replace_button = QtGui.QPushButton("Replace")
		self.replace_button = replace_button
		search_buttons_layout.addWidget(replace_button)
		replace_button.clicked.connect(self.replace)

		search_layout.addRow(search_buttons_layout)

		# TABLE
		results_table = QtGui.QTableWidget(0, 3)
		self.results_table = results_table
		search_layout.addRow(results_table)

		results_table.setHorizontalHeaderLabels(("Object", "Property", "Expression"))
		sizePolicy=QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
		sizePolicy.setHorizontalStretch(1)
		sizePolicy.setVerticalStretch(1)
		results_table.setSizePolicy(sizePolicy) # type: ignore
		results_table.horizontalHeader().setStretchLastSection(True)
		results_table.horizontalHeader().setDefaultSectionSize(100)
		results_table.setWordWrap(True)

		results_table.horizontalHeader().sectionResized.connect(self.resize_rows)
		# disabled editing of cells
		results_table.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
		results_table.cellClicked.connect(self.table_cell_clicked)

	def resize_rows(self):
		self.results_table.resizeRowsToContents()

	def search_for_expressions(self, callback =None):
		w_spreadsheet = self.include_spreadsheets.checkState()
		w_spreadsheet_expressions = self.include_spreadsheet_expressions.checkState()
		w_spreadsheet_aliases = self.include_spreadsheet_aliases.checkState()
		search_global = self.search_globally.checkState()
		search_for_expressions(
			w_spreadsheet,
			w_spreadsheet_expressions,
			w_spreadsheet_aliases,
			search_global,
			callback
		)

	def check_all(self):
		replacement=self.replace_term.text()
		show_replace=len(replacement) > 0
		if show_replace:
			for i in range(self.results_table.rowCount()):
				cell=self.results_table.cellWidget(i, 0)
				cell.setChecked(True)

	def uncheck_all(self):
		replacement=self.replace_term.text()
		show_replace=len(replacement) > 0
		if show_replace:
			for i in range(self.results_table.rowCount()):
				cell=self.results_table.cellWidget(i, 0)
				cell.setChecked(False)

	def replace(self):
		name=self.search_term.text()
		replacement=self.replace_term.text()
		def search(i, doc, o, prop, exp, type):
			cell=self.results_table.cellWidget(i, 0)
			if cell.isChecked() == False:
				return
			if name in exp:
				new_expression=exp.replace(name, replacement)
				print(prop, name, exp, new_expression)
				if o.TypeId == "Spreadsheet::Sheet":
					cell = prop
					if type == "cell-alias":
						o.setAlias(cell[0: -len("(alias)")], new_expression)
					if type == "cell-exp" or type == "cell":
						o.set(cell, new_expression)
				else:
					o.setExpression(prop, new_expression)

		for i, entry in enumerate(self.results):
			[doc, o, prop, exp, type]=entry
			search(i, doc, o, prop, exp, type)

		self.search()  # refresh

	def search(self):
		name=self.search_term.text()
		replacement=self.replace_term.text()
		search_global=self.search_globally.checkState()
		found=[]
		show_replace=len(replacement) > 0

		self.results=[]
		def search(i, doc, o, prop, exp, type):
			if name in exp:
				self.results.append([doc, o, prop, exp, type])
				item=[o.Label, prop, exp]
				if search_global:
					item.insert(0, doc)
				if show_replace:
					item.append(exp.replace(name, replacement))
				found.append(item)

		self.search_for_expressions(search)

		header=["Obj", "Prop", "Exp"]
		add_column=0
		if search_global:
			header.insert(0, "Doc")
		if show_replace:
			header.insert(0, "[ ]")  # checkbox
			header.insert(len(header), "Replacement")
			add_column=1

		same_cols=self.results_table.columnCount() == len(header)
		same_rows=self.results_table.rowCount() == len(found)

		if not same_cols:
			self.results_table.clear()
		self.results_table.setRowCount(len(found))
		self.results_table.setColumnCount(len(header))
		self.results_table.setHorizontalHeaderLabels(tuple(header))

		for row, item in enumerate(found):
			if show_replace and (not same_cols or not same_rows):
				checkbox=QtGui.QCheckBox("")
				checkbox.setChecked(True)
				self.results_table.setCellWidget(row, 0, checkbox)
			for col, part in enumerate(item):
				newItem=QtGui.QTableWidgetItem(part)
				self.results_table.setItem(row, col + add_column, newItem)

		if show_replace:
			self.results_table.setColumnWidth(0, 10)

		self.results_table.resizeRowsToContents()
		# self.aliasResultsTable.resizeColumnsToContents()
	def table_cell_clicked(self, row, col):
		doFocus=self.focus_object_on_sel.checkState()
		if not doFocus:
			return
		item=self.results[row]
		doc=item[0]
		o=item[1]
		App.setActiveDocument(doc)
		App.ActiveDocument=App.getDocument(doc)
		Gui.ActiveDocument=Gui.getDocument(doc)
		Gui.Selection.clearSelection() # type: ignore
		Gui.Selection.addSelection(o) # type: ignore
		Gui.SendMsgToActiveView("ViewSelection")


