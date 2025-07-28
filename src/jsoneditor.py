from src.fileio import FileIO
from tkinter import ttk, Label, Entry, Frame, Button, StringVar, END, LEFT, RIGHT
import importlib
import json
import os
import src.config
import src.jsoneditor
import string
import sys
import tkinter as tk
import subprocess

class JsonEditor(ttk.Treeview):

	def __init__(self, master, savefile=None, flat=False, columns=[], callback=None, **kw):
		super().__init__(master, selectmode="extended", **kw)

		self.master = master
		self.callback = callback
		self.flat = flat
		self.columns = columns
		self.createEvents()

		self.initialize()
		self.setSavefile(savefile)

	def initialize(self):
		self.nodes = []
		self.reordered = False

		if self.columns:
			self.column("#0", width=200, stretch=False)
		else:
			self.column("#0", width=200, stretch=False)
		if self.columns:
			self["columns"] = self.columns
			for column in self.columns:
				self.column(column, width=200, stretch=False)
				self.heading(column, text=column)
			self.column(column, width=300, stretch=True)

		self.entry_edit = None

	def setSavefile(self, savefile):
		self.savefile = savefile
		if self.savefile:
			
			self.initialize()
			self.loadSavefile()
			self.createNodes()

	def insert(self, **kw):
		super().insert(**kw)

	def loadSavefile(self):
		if os.path.exists(self.savefile):
			self.nodes = FileIO.loadJson(self.savefile)

	def saveSavefile(self):
		FileIO.saveJson(self.savefile, self.nodes)

	def createNodes(self):

		for node_id in self.get_children():
			self.delete(node_id)

		def addNodes(parent=None):
			childrennodes = []
			for node in self.nodes:
				if parent and node.get("parent") != parent:
					continue
				if not parent and node.get("parent"):
					continue
				childrennodes.append(node)
			childrennodes = sorted(childrennodes, key=lambda d: d.get('ordering'))
			for node in childrennodes:
				values = [node.get(colname) for colname in self.columns]
				parent = node.get("parent") if node.get("parent") else ""
				opened = node.get("opened")
				self.insert(parent=parent, index="end", iid=node.get("id"), text=node.get("label"), values=values)
				self.item(node.get("id"), open=opened)
				addNodes(node.get("id"))

		addNodes()

	def createEvents(self):
		self.bind("<ButtonPress-1>", self.bDown)
		self.bind("<ButtonRelease-1>", self.bUp, add='+')
		self.bind("<B1-Motion>", self.bMove, add='+')
		self.bind("<Double-1>", self.bDblClick, add='+')
		self.bind("<Triple-1>", self.bTplClick, add='+')
		self.bind("<F2>", self.bRename, add='+')
		self.bind("<<TreeviewOpen>>", self.bTreeviewOpen, add='+')
		self.bind("<<TreeviewClose>>", self.bTreeviewClose, add='+')
		self.bind("<Return>", self.bEnter, add='+')

	def bDown(self, event):
		self.region_clicked = self.identify_region(event.x, event.y)
		if self.region_clicked == "nothing":
			self.selection_set()
		self.exitTextEditor()

	def bUp(self, event):
		if self.reordered:
			print("saveReordering")
			self.saveReordering()

	def bMove(self, event):
		moveto = self.index(self.identify_row(event.y))
		for sel in self.selection():
			if self.parent(self.identify_row(event.y)) == self.parent(sel):
				self.move(sel, self.parent(sel), moveto)
				self.reordered = True
			break

	def bDblClick(self, event):
		self.column_clicked = self.identify_column(event.x)
		self.column_clicked_int = int(self.column_clicked[1:])
		if not self.column_clicked_int:
			self.executeSelected()
		else:
			self.selected_iid = self.focus()
			self.sel_bbox = self.bbox(self.selected_iid, self.column_clicked)
			self.obtype = self.getNodeById(self.selected_iid).get("obtype")
			if (self.obtype == "folder" and not self.column_clicked_int) or self.obtype == "file":
				self.createTextBox(event)

	def bTplClick(self, event):
		self.column_clicked = self.identify_column(event.x)
		self.column_clicked_int = int(self.column_clicked[1:])
		if not self.column_clicked_int:
			self.selected_iid = self.focus()
			self.sel_bbox = self.bbox(self.selected_iid, self.column_clicked)
			self.obtype = self.getNodeById(self.selected_iid).get("obtype")
			if (self.obtype == "folder" and not self.column_clicked_int) or self.obtype == "file":
				self.createTextBox(event)

	def bRename(self, event):
		self.column_clicked = self.identify_column(event.x)
		self.column_clicked_int = int(self.column_clicked[1:])
		self.selected_iid = self.focus()
		self.sel_bbox = self.bbox(self.selected_iid, self.column_clicked)
		self.obtype = self.getNodeById(self.selected_iid).get("obtype")
		if (self.obtype == "folder" and not self.column_clicked_int) or self.obtype == "file":
			self.createTextBox(event)

	def bTreeviewOpen(self, event):
		selected_iid = self.focus()
		node = self.getNodeById(selected_iid)
		node["opened"] = True
		self.saveSavefile()

	def bTreeviewClose(self, event):
		selected_iid = self.focus()
		node = self.getNodeById(selected_iid)
		node["opened"] = False
		self.saveSavefile()

	def bEnter(self, event):
		self.executeSelected()

	def executeSelected(self, event=None):
		self.focus_set()
		for sel in self.selection():
			if self.callback:
				if not self.get_children(sel):
					node = self.getNodeById(sel)
					self.callback("execute", node)
		
	def exitTextEditor(self, discard_changes=False):
		if self.entry_edit:
			node = self.getNodeById(self.selected_iid)
			if not discard_changes:
				print("Renaming {} to {}".format(self.column_clicked_text, self.entry_edit.get()))
				node[self.column_clicked_text] = self.entry_edit.get()
				self.saveSavefile()
				self.callback("rename", node)
			values = [node.get(colname) for colname in self.columns]
			self.item(self.selected_iid, text=node["label"], values=values)
			self.entry_edit.destroy()
			self.entry_edit = None
			self.focus_set()

	def saveReordering(self):
		selected_iid = self.focus()
		ordering = 1
		for node_id in self.get_children(self.parent(selected_iid)):
			node = self.getNodeById(node_id)
			node["ordering"] = ordering
			ordering += 1
		self.saveSavefile()
		self.reordered = False

	def getNodeById(self, nodeid):
		for node in self.nodes:
			if str(node["id"]) == str(nodeid):
				return node

	def genNewNodeId(self):
		node_ids = [int(node["id"]) for node in self.nodes]
		if len(node_ids):
			return str(int(max(node_ids)) + 1)
		return "1"

	def genNewOrdering(self, parent):
		orderings = [int(node["ordering"]) for node in self.nodes if node["parent"] == parent]
		if len(orderings):
			return int(max(orderings)) + 1
		return 1

	def createTextBox(self, event):
		if not self.column_clicked_int:
			self.column_clicked_text = "label"
		else:
			self.column_clicked_text = self.columns[self.column_clicked_int - 1]
		node = self.getNodeById(self.selected_iid)
		text = node.get(self.column_clicked_text) if self.column_clicked_text in node else ""
		self.node_values = self.item(self.selected_iid).get("values")

		self.entry_edit = Entry(self.master, width=self.sel_bbox[2])
		self.entry_edit.insert(0, text)
		self.entry_edit.select_range(0, END)
		self.entry_edit.focus()
		def bSave(event):
			self.exitTextEditor()
		def bDiscard(event):
			self.exitTextEditor(True)
		self.entry_edit.bind("<Return>", bSave)
		self.entry_edit.bind("<FocusOut>", bSave)
		self.entry_edit.bind("<Escape>", bDiscard)
		if not self.column_clicked_int:
			padding = 18
		else:
			padding = 2
		self.entry_edit.place(x=self.sel_bbox[0]+padding, y=self.sel_bbox[1], width=self.sel_bbox[2], height=self.sel_bbox[3])

	def addItem(self, obtype="folder", custom_attrs={}):
		selected_iid = self.focus()
		selnode = self.getNodeById(selected_iid)
		self.item(selected_iid, open=True)
		if self.selection():
			parent = selected_iid
			if self.flat:
				parent = ""
			if selnode["obtype"] == "file":
				parent = selnode["parent"]
			idx = self.genNewOrdering(parent)
		else:
			parent = ""
			idx = self.genNewOrdering(parent)
		text = ""
		node = {
			"parent": parent,
			"opened": True,
			"label": text,
			"obtype": obtype,
			"ordering": idx
		}
		for column in self.columns:
			node[column] = ""
		node = {**node, **custom_attrs}
		node["id"] = self.genNewNodeId()
		node["ordering"] = idx
		self.callback("add", node)
		self.nodes.append(node)
		self.saveSavefile()
		values = [node.get(colname) for colname in self.columns]
		self.insert(parent=node["parent"], index=idx, iid=node["id"], text=node["label"], values=values)
		self.focus_set()
		self.selection_set(node["id"])
		return node

	def addFolderItem(self):
		custom_attrs = {
			"obtype": "folder"
		}
		self.addItem(obtype="folder")

	def addFileItem(self):
		custom_attrs = {
			"obtype": "file"
		}
		self.addItem(obtype="file")

	def duplicateItem(self):
		self.focus_set()
		for selected_iid in self.selection():
			node = self.getNodeById(selected_iid)
			node = self.addItem(obtype=node["obtype"], custom_attrs=node.copy())
			self.selection_set(node["id"])
			self.focus(node["id"])
		self.focus_set()

	def delItem(self, event=None):
		self.focus_set()
		for selected_iid in self.selection():
			nextsel = self.next(selected_iid)
			if not nextsel:
				nextsel = self.prev(selected_iid)
			if not nextsel:
				nextsel = self.parent(selected_iid)
			if not nextsel:
				nextsel = ""
			self.next(selected_iid)
			self.delete(selected_iid)
			node = self.getNodeById(selected_iid)
			self.callback("delete", node)
			self.nodes.remove(node)
			self.selection_set(nextsel)
			self.focus(nextsel)
		self.saveSavefile()
		self.focus_set()
