


import math
import os
import __main__
import re
import FreeCAD as App
import ImportGui
import importSVG
import Mesh
import Part
import MeshPart
from PySide import QtCore, QtGui
from .utils import get_all_objects
from pathlib import Path

custom_params_regex = re.compile("Export(?:\\((.*?)\\))?(?:@\\(\s*?([0-9.]+)\s*?,\s*?([0-9,]+)\\s*?\\))?")
class ExportTab(QtGui.QWidget):

	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		export_layout = QtGui.QFormLayout(self)
		export_layout.setContentsMargins(QtCore.QMargins(0, 5, 0, 5))

		export_type = QtGui.QLineEdit("stl")
		self.export_type = export_type
		export_layout.addRow("Mesh Export File Type", export_type) # type: ignore
		export_type.textChanged.connect(self.check_show_stl_opts)

		# STL Export Options
		self.stl_options_widget = QtGui.QWidget()
		export_layout.addWidget(self.stl_options_widget)
		stl_options_layout = QtGui.QFormLayout(self.stl_options_widget)
		stl_options_layout.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))
		self.stl_opt_surface_deviation = QtGui.QLineEdit("0.5")
		tooltip = "This is the same option found when using the Mesh Workbench using the standard exporter."
		self.stl_opt_surface_deviation.setToolTip(tooltip)
		self.stl_opt_angular_deviation = QtGui.QLineEdit("1.0")
		self.stl_opt_angular_deviation.setToolTip(tooltip)
		stl_options_layout.addRow("Surface Deviation (in mm)", self.stl_opt_surface_deviation)  # type: ignore
		stl_options_layout.addRow("Angular Deviation (in deg)", self.stl_opt_angular_deviation)  # type: ignore

		self.export_location = QtGui.QLineEdit("exports")
		export_layout.addRow("Export Location", self.export_location) # type: ignore

		button_layout = QtGui.QHBoxLayout(self)
		export_layout.addRow(button_layout)
		button_layout.setContentsMargins(QtCore.QMargins(0, 0, 0, 0))

		relative_export = QtGui.QCheckBox("Relative to Active File")
		relative_export.setChecked(False)
		self.relative_export = relative_export
		button_layout.addWidget(relative_export)  # type: ignore

		search_globally = QtGui.QCheckBox("From All Documents")
		self.search_globally = search_globally
		button_layout.addWidget(search_globally)
		search_globally.setChecked(False)

		export_all_marked_button = QtGui.QPushButton("Export All Marked")
		self.export_all_marked_button = export_all_marked_button
		export_all_marked_button.setToolTip("To Mark a part for exporting, it's `Label2` property must include the word `Export`/`export`.")
		export_all_marked_button.clicked.connect(self.export_all_marked)
		export_layout.addRow(export_all_marked_button)

		self.results = []
	def is_stl_export(self):
		type = self.export_type.text()
		if (type == "stl"):
			return True
		return False
	def check_show_stl_opts(self):
		if self.is_stl_export():
			self.stl_options_widget.show()
		else:
			self.stl_options_widget.hide()


	def export_all_marked(self):
		export_location = self.export_location.text()
		is_stl_export = self.is_stl_export()
		mesh_export_type = self.export_type.text()
		surface_deviation = None
		angular_deviation = None
		if (is_stl_export):
			surface_deviation = float(self.stl_opt_surface_deviation.text())
			angular_deviation = float(self.stl_opt_angular_deviation.text()) * math.pi / 180
		search_globally = self.search_globally.checkState()
		objects = get_all_objects(search_globally)
		cannot_export = []
		for doc, obj in objects:
			if "Export" in obj.Label2 or "export" in obj.Label2:
				try:
					obj.touch()
				except Exception as e:
					print(e)
					cannot_export.append(obj)
		App.ActiveDocument.recompute()
		for doc, obj in objects:
			params_surface_deviation = None 
			params_angular_deviation = None
			if "Export" in obj.Label2 or "export" in obj.Label2:
				export_type = mesh_export_type 
				is_already_mesh =  isinstance(obj, Mesh.Feature)
				is_sketch = obj.isDerivedFrom("Sketcher::SketchObject")
				if is_sketch:
					export_type = "svg"

				custom = custom_params_regex.search(obj.Label2)
				if custom.group(2) and custom.group(3):
					try:
						params_surface_deviation = float(custom.group(2))
						params_angular_deviation = float(custom.group(3))
					except ValueError:
						print(obj.Label + ": Could not export, error parsing custom params as floats: " +  custom.group(2)+ " and " + custom.group(3))
						continue

				name = None
				if custom.group(1):
					name = custom.group(1)
					if (name[0] == "="):
						obj_name = name[1:]
					else: 
						suffix = "-" + name
						obj_name = doc + "-" + obj.Label + suffix
				else:
					obj_name = doc + "-" + obj.Label

				if (obj in cannot_export):
					print(obj_name + "has errors, cannot export.")
					continue
				current_dir = os.path.dirname(App.getDocument(doc).FileName) # type: ignore
				directory = os.path.join(current_dir, export_location + "/")
				filename = os.path.join(directory + obj_name + "." + export_type)
				Path(directory).mkdir(parents=True, exist_ok=True)
				try:
					if os.path.exists(filename):
						os.remove(filename)
					if is_sketch:
						importSVG.export([obj],filename)
					elif (is_already_mesh):
						Mesh.export([obj], filename)
					elif (is_stl_export):
						mesh = App.getDocument(doc).addObject("Mesh::Feature", "Mesh") # type: ignore
						shape = Part.getShape(obj)
						mesh.Mesh = MeshPart.meshFromShape(
							Shape=shape,
							LinearDeflection=params_surface_deviation or surface_deviation,
							AngularDeflection=params_angular_deviation or angular_deviation,
							Relative=True
						)
						Mesh.export([mesh], filename)
						App.ActiveDocument.removeObject(mesh.Name)
					else:
						ImportGui.export([obj], filename)

					print("Exported: " + filename)
					if (params_surface_deviation or params_angular_deviation):
						print("\twith overriden params: SurfaceDeviation: " + str(params_surface_deviation) + " AngularDeviation: " + str(params_angular_deviation))	
				except Exception as e:
					print("Failed to export: " + obj_name)
					print(e)
