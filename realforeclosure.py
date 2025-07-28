"""
scriptsmanager.py version 20231215

Dependencies:
pipreqs
pip install -r requirements.txt

Install:
See README

Example usage:
python scriptsmanager.py
"""

from idlelib import pyshell
from src.fileio import FileIO
from src.tk_datepicker import Datepicker
from threading import Thread, Event
from tkinter import ttk, END, TOP, BOTTOM, LEFT, RIGHT, VERTICAL, HORIZONTAL, N, S, ALL
from tkinter import ttk, Label, Entry, Frame, Button, Text, Listbox, StringVar, Scrollbar, Checkbutton, Canvas
from tkinter.scrolledtext import ScrolledText
from tkinter.ttk import *
from src.ttkscrollableframe import ScrollableFrame
from typing import Dict
import argparse
import datetime
import importlib
import json
import keyboard
import more_itertools
import os
import psutil
import pygetwindow
import pywinctl as pwc
import src.browser
import src.cmdscript
import src.config
import src.excel
import src.jsoneditor
import src.network
import src.simplefilesystemcacher
import src.simplemysqlcacher
import src.ttkels
import src.threader
import src.scraper
import string
import subprocess
import sys
import time
import tkinter
import tkinter as tk
import subprocess
import traceback
from threading import Thread, Event, Lock
from queue import Queue

class Manager : 

	def cmdOutputClear(self):
		self.log.delete('1.0', END)
		self.log.see(END)

	def cmdOutputLine(self, line, overwrite=False):
		if not overwrite:
			self.log.insert("end", u"\n{}".format(line[:97]))
		else:
			self.log.delete("end-1l", "end")
			self.log.insert("end", u"\n{}".format(line[:97]))
		self.log.see(END)

	def __init__(self):

		self.config = src.config.Config()
		self.workingdir = os.path.dirname(__file__)
		self.themesdir = self.workingdir+"/awthemes-10.4.0"

		self.settings = {
			"theme": "awdark",
			"remainopen": True
		}

		self.root = tk.Tk()
		self.root.grid_columnconfigure(0, weight=1)
		self.root.grid_rowconfigure(0, weight=1)
		self.root.geometry("800x600+100+100")
		self.root.winfo_toplevel().title("RealForeclose Bot")
		self.root.wm_iconbitmap('realtaxdeed-logo.ico')

		self.loadSettings()
		self.createStyle()
		self.createLayoutShell()
		self.createLayoutLog()
		self.createLayoutForm()

		def exitProgram():
			self.root.quit()
			subprocess.Popen("python realtaxdeed.py", shell=True)
		keyboard.add_hotkey('alt+r', exitProgram)

		self.root.mainloop()

	def createStyle(self):
		themenames = [
			"awdark",
			"awlight",
		]
		self.root.tk.call('lappend', 'auto_path', self.themesdir)
		self.root.tk.call('package', 'require', 'awthemes')
		for themename in themenames:
			self.root.tk.call('package', 'require', themename)

		style = ttk.Style()
		style.theme_use(themenames[0])

	def createLayoutShell(self):
		self.framemaintop = src.ttkels.TkinterRow(self.root)
		self.framemaintopright = src.ttkels.TkinterColumn(self.framemaintop, column=1)
		self.framemaintoprighttop = src.ttkels.TkinterRow(self.framemaintopright)
		self.framemaintoprightbottom = src.ttkels.TkinterRow(self.framemaintopright, is_table=True, row=1, scrollable=False, sticky="nsw", height=200)
		self.framemainbottom = src.ttkels.TkinterRow(self.root, row=1)
		self.framemainbottomright = src.ttkels.TkinterColumn(self.framemainbottom, column=1)
		self.framemaintoprightbottom.grid_columnconfigure(0, weight=5)
		self.framemaintoprightbottom.grid_columnconfigure(1, weight=2)
		self.framemaintoprightbottom.grid_columnconfigure(2, weight=2)
		self.framemaintoprighttop.grid(padx=(15, 5), pady=(5, 0))

	def getDataDir(self):
		data_fn = os.path.join(".")
		if not os.path.exists(data_fn):
			os.makedirs(data_fn)
		return data_fn

	def getSettingsFn(self):
		settings_fn = os.path.join(self.getDataDir(), "settings.json")
		return settings_fn

	def getResultsDir(self):
		data_fn = os.path.join(self.getDataDir(), "results")
		if not os.path.exists(data_fn):
			os.makedirs(data_fn)
		return data_fn

	def loadSettings(self):
		self.settings = {}
		if os.path.exists(self.getSettingsFn()):
			self.settings = FileIO.loadJson(self.getSettingsFn())
		if not "themename" in self.settings:
			self.settings["themename"] = "awdark"
		if not "counties" in self.settings:
			self.settings["counties"] = []
			supported_counties = ["Orange", "Hillsborough", "Palm Beach", "Walton", "Okaloosa", "Santa Rosa", "Duvall", "Duvall", "Broward", "Escambia"]
			counties = FileIO.loadJson("counties.json")
			for county in counties:
				county_id, county_name, county_sel = county
				self.settings["counties"].append([county_id, county_name, 1])
		if not "start_date" in self.settings:
			self.settings["start_date"] = None
		if not "end_date" in self.settings:
			self.settings["end_date"] = None

	def saveSettings(self):
		FileIO.saveJson(self.getSettingsFn(), self.settings)

	is_started = False
	def doContinuousUpdates(self):
		while(self.is_started):
			self.root.update()
			time.sleep(.1)

	def doExport(self):
		try:

			self.config = src.config.Config()
			self.net = src.network.Network(proxy=self.config.proxy)
			self.netresi = src.network.Network(proxy=self.config.proxy_resi)
			self.netraw = src.network.Network()
			self.excel = src.excel.Excel(self)
			self.scheduler = src.threader.Scheduler(thread_count=self.config.thread_count)

			def getCountyDomain(county_name):
				county_type = county_name.split(" ")[-1].lower()
				county_name = "".join(county_name.split(" ")[0:-1]).lower()

			counties = [county[0] for county in self.settings["counties"] if county[2]]
			start_date = self.start_date.get()
			end_date = self.end_date.get()

			importlib.reload(src.scraper)
			self.scraper = src.scraper.Scraper(self, counties, start_date, end_date)

			if "selected" in self.inc_auc.state():
				self.scraper.doExportAuctions()

			if "selected" in self.inc_res.state():
				self.scraper.doExportResults()

		except Exception as exc:
			if False:
				self.cmdOutputLine(str(exc))
			else:
				self.cmdOutputLine(traceback.format_exc())
		self.doComplete()

	def doStart(self):
		self.is_started = True
		self.cmdOutputClear()
		self.cmdOutputLine("Starting")
		self.stop_btn.state(["!disabled"])
		self.start_btn.state(["disabled"])

		thread = Thread(target=self.doExport)
		thread.start()

	def doComplete(self):
		self.is_started = False
		self.cmdOutputLine("Complete")
		self.stop_btn.state(["disabled"])
		self.start_btn.state(["!disabled"])

	def doStop(self):
		self.is_started = False
		self.cmdOutputLine("Stopping")
		self.stop_btn.state(["disabled"])
		self.start_btn.state(["!disabled"])

	def doSettings(self):
		pass

	def doViewResults(self):
		command = r'''explorer "{}"'''.format(self.getResultsDir())
		subprocess.Popen(command)

	def createLayoutForm(self):
		self.framemaintoprightbottomoptions = src.ttkels.TkinterColumn(self.framemaintoprightbottom, is_table=True, column=0)
		self.framemaintoprightbottomoptions.grid(padx=(20, 20), pady=(20, 20))
		self.framemaintoprightbottomcalendar1 = src.ttkels.TkinterColumn(self.framemaintoprightbottom, is_table=True, column=1)
		self.framemaintoprightbottomcalendar1.grid(padx=(0, 20), pady=(20, 20))
		self.framemaintoprightbottomcalendar2 = src.ttkels.TkinterColumn(self.framemaintoprightbottom, is_table=True, column=2)
		self.framemaintoprightbottomcalendar2.grid(padx=(0, 20), pady=(20, 20))

		self.start_btn = src.ttkels.TkinterBtn(self.framemaintoprighttop, text="Start", command=self.doStart)
		self.stop_btn = src.ttkels.TkinterBtn(self.framemaintoprighttop, text="Stop", command=self.doStop)
		self.stop_btn.state(["disabled"])

		self.inc_auc = ttk.Checkbutton(self.framemaintoprighttop, text="Include Auctions", onvalue=1, offvalue=0)
		self.inc_auc.pack(expand=False, fill='x', side=LEFT, pady=(5, 0))
		self.inc_auc.state(["selected"])

		self.inc_res = ttk.Checkbutton(self.framemaintoprighttop, text="Include Results", onvalue=1, offvalue=0)
		self.inc_res.pack(expand=False, fill='x', side=LEFT, pady=(5, 0))
		self.inc_res.state(["selected"])

		self.view_btn = src.ttkels.TkinterBtn(self.framemaintoprighttop, text="View Results", command=self.doViewResults)
		self.view_btn.pack(expand=False, fill='y', side=RIGHT)


		gridalignouter = tkinter.Frame(self.framemaintoprightbottomoptions, width=192)
		gridalignouter.pack(expand=True, fill='y', side=TOP, pady=(5, 0))

		gridalign = Frame(self.root)
		gridalign.place(x=20, y=62)

		canvas = tkinter.Canvas(gridalign, width=184, height=272, bg="#33393b", borderwidth=0, highlightthickness=0)
		scrollbar = Scrollbar(gridalign, orient="vertical", command=canvas.yview)
		gridalign.scrollable_frame = Frame(canvas)

		def _on_mousewheel(event):
			canvas.yview_scroll(int(-1*(event.delta/120)), "units")
		canvas.bind_all("<MouseWheel>", _on_mousewheel)

		gridalign.scrollable_frame.bind(
			"<Configure>",
			lambda e: canvas.configure(
				scrollregion=canvas.bbox("all")
			)
		)

		canvas.create_window((0, 0), window=gridalign.scrollable_frame, anchor="nw")
		canvas.configure(yscrollcommand=scrollbar.set)
		canvas.pack(side="left", fill="both", expand=True)
		scrollbar.pack(side="right", fill="y")

		options = []

		def optionOnChange(option):
			if "Select" in option.cget("text") or not option.cget("text"):
				new_selected = 1 if "selected" in option.state() else 0
				for option in options:
					option.state(["selected" if new_selected else "!selected"])
					for county in self.settings["counties"]:
						if county[1] == option.cget("text"):
							county[2] = (1 if new_selected else 0)
				self.saveSettings()
			else:
				for county in self.settings["counties"]:
					if county[1] == option.cget("text"):
						county[2] = 1 if "selected" in option.state() else 0
				self.saveSettings()

		def generateOption(county_x, county):
			county_id, county_name, county_sel = county
			option = ttk.Checkbutton(gridalign.scrollable_frame, text=county_name, onvalue=1, offvalue=0)
			option.configure(command=lambda: optionOnChange(option))
			option.pack(expand=True, fill='x', side=TOP, pady=(5, 0))
			option.state(["selected" if county_sel else "!selected"])
			options.append(option)

		generateOption(0, [0, "Select", 1])
		for county_x, county in enumerate(self.settings["counties"]):
			county_id, county_name, county_sel = county
			generateOption(county_x, county)


		def startDateOnChange():
			if self.start_date.get():
				self.settings["start_date"] = self.start_date.get()
				self.saveSettings()

		sv = StringVar()
		sv.trace("w", lambda name, index, mode, sv=sv: startDateOnChange())
		self.start_date = Entry(self.framemaintoprightbottomcalendar1, width=31, textvariable=sv)
		self.start_date.grid(row=0, column=0, sticky="w")
		Datepicker(self.start_date, self.settings["start_date"])

		def endDateOnChange():
			if self.start_date.get():
				self.settings["end_date"] = self.end_date.get()
				self.saveSettings()

		sv = StringVar()
		sv.trace("w", lambda name, index, mode, sv=sv: endDateOnChange())
		self.end_date = Entry(self.framemaintoprightbottomcalendar2, width=31, textvariable=sv)
		self.end_date.grid(row=0, column=0, sticky="w")
		Datepicker(self.end_date, self.settings["end_date"])


	def createLayoutLog(self):
		self.log = Text(self.framemainbottomright, wrap="none", bg="black", fg="white", padx=3, pady=3, height=15)
		self.log.config(highlightthickness=0, highlightbackground = "black", highlightcolor= "black")
		self.log.grid(row=0, column=0, sticky="nsew")
		scrollbar = src.ttkels.TkinterScrollbar(self.log.master, self.log, orient=VERTICAL)

if __name__ == '__main__':
	man = Manager()