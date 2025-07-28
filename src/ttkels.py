
from src.fileio import FileIO
import tkinter
from tkinter import ttk, Label, Entry, Frame, Button, Text, Listbox, StringVar, Scrollbar
from tkinter import ttk, END, TOP, BOTTOM, LEFT, RIGHT, VERTICAL, HORIZONTAL, N, S
from tkinter.ttk import *
from typing import Dict
import importlib
import json
import os
import src.config
import src.jsoneditor
import src.cmdscript
import string
import sys
import tkinter as tk
import traceback
import keyboard
import subprocess
import psutil
import pygetwindow
import time

class TkinterRow(Frame):

	def __init__(self, master, is_table=True, scrollable=False, sticky="nsew", row=0, column=0, **kw):
		super().__init__(master, **kw)

		self.master = master

		self.grid(row=row, column=column, sticky=sticky)
		if is_table:
			self.grid_rowconfigure(0, weight=1)
			self.grid_columnconfigure(0, weight=0)
			self.grid_columnconfigure(1, weight=5)
		if scrollable:
			self.grid_rowconfigure(0, weight=1)
			self.grid_columnconfigure(0, weight=5)
			self.grid_columnconfigure(1, weight=0)

class TkinterColumn(Frame):

	def __init__(self, master, is_table=True, row=0, column=0, **kw):
		super().__init__(master, **kw)

		self.master = master

		self.grid(row=row, column=column, sticky="nsew")
		if is_table:
			self.grid_columnconfigure(0, weight=1)
			self.grid_rowconfigure(0, weight=0)
			self.grid_rowconfigure(1, weight=5)

class TkinterBtn(Button):

	def __init__(self, master, **kw):
		super().__init__(master, **kw)

		self.master = master

		self.pack(padx=(0, 5), pady=(5, 0), expand=False, fill='y', side=LEFT)

class TkinterScrollbar(Scrollbar):

	def __init__(self, master, attachment, orient=VERTICAL, **kw):
		super().__init__(master, orient=orient, command=attachment.yview, **kw)

		self.master = master

		if orient == VERTICAL:
			self.grid(row=0, column=1, sticky="nsew")
			attachment.configure(yscrollcommand=self.set)
		else:
			self.grid(row=1, column=0, sticky="nsew")
			attachment.configure(xscrollcommand=self.set)