

import __main__
import FreeCADGui as Gui

import math
from PySide import QtGui
from .utils import monospace


class SelectionInfo(QtGui.QWidget):

	def __init__(self, layout: QtGui.QLayout):
		super().__init__()
		self.initUI(layout)
		self.observer = self.SelectionObserver(self)

	def initUI(self, layout):
		self.count_title_label = QtGui.QLabel(monospace("Selection Count: 0"))
		layout.addWidget(self.count_title_label)

		self.count_label = QtGui.QLabel("")
		self.count_label.setVisible(False)
		layout.addWidget(self.count_label)

		self.distance_label = QtGui.QLabel("")
		self.distance_label.setVisible(False)
		layout.addWidget(self.distance_label)

	def set_selection_info(self, count, sum, distances, diameter):

		self.count_title_label.setText(monospace("Selection Count:" + count))
		radius_text = ""
		if (diameter != None):
			radius_text = "Diameter: "+ diameter + "mm" + "\n"
		self.count_label.setText(monospace(
			sum + "mm Selected" + "\n" +
			radius_text
		))
		self.count_label.setVisible(True)
		if distances is not None:
			self.distance_label.setVisible(True)
			(distance, x_distance, y_distance, z_distance,
				xmin_distance, ymin_distance, zmin_distance,
				xmax_distance, ymax_distance, zmax_distance) = distances
			self.distance_label.setText(monospace(
				"Distance: " + distance + " mm" + "\n" +
				"X " + x_distance + " mm (Min: " + xmin_distance + " mm, Max: " + xmax_distance + " mm)" + "\n" +
				"Y " + y_distance + " mm (Min: " + ymin_distance + " mm, Max: " + ymax_distance + " mm)" + "\n" +
				"Z " + z_distance + " mm (Min: " + zmin_distance + " mm, Max: " + zmax_distance + " mm)" + "\n"
			))
		else:
			self.distance_label.setText("")
			self.distance_label.setVisible(False)

	def set_no_selection(self):
		self.count_title_label.setText(monospace("Selection Count: 0"))
		self.count_label.setVisible(False)
		self.distance_label.setVisible(False)

	class SelectionObserver:
		def __init__(self, widget):
			self.widget = widget
			self.disableObserver = False

		def addSelection(self, doc, obj, sub, pnt): #noaq N802
			self.check_selection()

		def removeSelection(self, doc, obj, sub):
			self.check_selection()

		def setSelection(self, doc):
			self.check_selection()

		def clearSelection(self, doc):
			self.check_selection()

		def check_selection(self):
			gui_selections = Gui.Selection.getSelectionEx('', 0) #type: ignore

			def round_to(n, x=1000):
				# shrink very long numbers to scientific notation
				# these large numbers can happen when selecting an LCS since it's bounding box seems to be of infinite dimensions.
				if (n > 1000000000):
					[num, exp] = "{:.3e}".format(n).split("e")
					num = float(num)
					num = "{:.3f}".format(math.ceil(num * x) / x).rstrip('0').rstrip('.')
					exp = "x10<sup>" + exp.replace("+", "") + "</sup>"
					return num + exp
				return "{:.3f}".format(math.ceil(n * x) / x).rstrip('0').rstrip('.')

			sel_count = 0
			for sel in gui_selections:
				if sel.SubElementNames:
					for path in sel.SubElementNames:
						sel_count += 1

			selections = []
			found_radius = None
			if len(gui_selections) == 0:
				self.widget.set_no_selection()
			else:
				for sel in gui_selections:
					if sel.SubElementNames:
						for path in sel.SubElementNames:
							# we cannot use sel.getSubObjects because the coordinates of the selections might not be global (i.e. part design selection, links, etc)
							# getGlobalPlacement cand be used for most cases, but is not reliable for links
							# this seems to get a subobject with global coordinates every time.
							try:
								obj = sel.Object.getSubObject(path, 0)
								if obj is None or obj.Length is None or obj.BoundBox is None:
									continue
							except RuntimeError:
								# shape is invalid, skip it
								continue
							if hasattr(obj, "Curve") and hasattr(obj.Curve, "Radius"):
								found_radius = obj.Curve.Radius
							selections.append(obj)

				sum = 0
				count = str(sel_count)

				for (obj) in selections:
					sum += obj.Length


				distances = None
				distance = None
				x_distance = None
				y_distance = None
				z_distance = None
				xmin_distance = None
				ymin_distance = None
				zmin_distance = None
				xmax_distance = None
				ymax_distance = None
				zmax_distance = None
				diameter = None
				if sel_count == 1 and found_radius:
					diameter = round_to(found_radius * 2)
				if len(selections) == 2:
					sel1 = selections[0].BoundBox
					sel2 = selections[1].BoundBox
					p1 = sel1.Center
					p2 = sel2.Center

					distance = round_to(p1.distanceToPoint(p2))
					x_distance = round_to(abs(p1.x - p2.x))
					y_distance = round_to(abs(p1.y - p2.y))
					z_distance = round_to(abs(p1.z - p2.z))

					xmin_distance = round_to(abs(sel1.XMin - sel2.XMin))
					xmax_distance = round_to(abs(sel1.XMax - sel2.XMax))
					ymin_distance = round_to(abs(sel1.YMin - sel2.YMin))
					ymax_distance = round_to(abs(sel1.YMax - sel2.YMax))
					zmin_distance = round_to(abs(sel1.ZMin - sel2.ZMin))
					zmax_distance = round_to(abs(sel1.ZMax - sel2.ZMax))

					distances = (distance, x_distance, y_distance, z_distance,
								xmin_distance, ymin_distance, zmin_distance,
								xmax_distance, ymax_distance, zmax_distance)


				sum = round_to(sum)
				self.widget.set_selection_info(
					count, sum, distances, diameter)
