
import tkinter
from tkinter import ttk, Label, Entry, Frame, Button, Text, Listbox, StringVar, Scrollbar
from tkinter import ttk, END, TOP, BOTTOM, LEFT, RIGHT, VERTICAL, HORIZONTAL, N, S
from tkinter.ttk import *
from datetime import datetime, timedelta

from tkinter import SOLID

class Datepicker(Frame):
    def __init__(self, input, first_date=None, button=None, *args, **kwargs):        
        super().__init__(input.master, *args, **kwargs)
        self.input = input
        self.ui_settings()

        self.CLOSE = 1
        self.WIDTH = 200
        self.HEIGHT = 200
        self.NOW = datetime.now()
        self.FIRST_DATE = None
        if first_date:
            try:
                self.FIRST_DATE = datetime.strptime(first_date, self.output_format).date()
            except:
                pass
        if not self.FIRST_DATE:
            self.FIRST_DATE = datetime(self.NOW.year, self.NOW.month, 1)
        self.input.insert(0, self.FIRST_DATE.strftime(self.output_format))

        pos = [input.master.master.winfo_x()+312, input.winfo_y()+59]
        pos = [0, 30]
        self._show(pos[0], pos[1])
    

    def __call__(self, event=None, *args, **kwargs):
        if event:
            x, y = self.get_start_point(event)
    
            if self.CLOSE:
                self._show(x, y)
            else:
                self._hide()


    def get_start_point(self, event):
        '''Return (x, y) start coord'''

        margin = 5

        widg_w = event.widget.winfo_width() # Widget width
        widg_h = event.widget.winfo_height() # Widget height
        root_w = self.master.winfo_width() # Root width
        root_h = self.master.winfo_height() # Root height

        p1 = {'x': event.widget.winfo_x(), 'y': event.widget.winfo_y()} # Left top point
        p2 = {'x': event.widget.winfo_x() + widg_w, 'y': event.widget.winfo_y()} # Right top point
        p3 = {'x': event.widget.winfo_x(), 'y': event.widget.winfo_y() + widg_h} # Left bottom point
        p4 = {'x': event.widget.winfo_x() + widg_w, 'y': event.widget.winfo_y() + widg_h} # Right bottom point

        x, y = None, None

        if p1['x'] > self.WIDTH: # LEFT CENTER
            x = p1['x'] - margin - self.WIDTH
            y = (p3['y'] - p1['y']) // 2 + p1['y'] - self.HEIGHT // 2

        if root_w - p2['x'] > self.WIDTH: # RIGHT CENTER
            x = p2['x'] + margin
            y = (p4['y'] - p2['y']) // 2 + p2['y'] - self.HEIGHT // 2


        if root_h - p3['y'] > self.HEIGHT: # BOTTOM
            if p3['x'] > self.WIDTH // 2 and root_w - p4['x'] > self.WIDTH // 2: # CENTER
                x = (p4['x'] - p3['x']) // 2 + p3['x'] - (self.WIDTH // 2)
                y = p3['y'] + margin
            elif p3['x'] > self.WIDTH: # LEFT
                x = p3['x'] - self.WIDTH - margin
                y = p3['y'] - margin
            elif root_w - p3['x'] > self.WIDTH: # RIGHT
                x = p4['x'] + margin
                y = p4['y'] + margin
        
        if p1['y'] > self.HEIGHT: # TOP
            if p1['x'] > self.WIDTH // 2 and root_w - p2['x'] > self.WIDTH // 2: # CENTER
                x = (p2['x'] - p1['x']) // 2 + p1['x'] - (self.WIDTH // 2)
                y = p1['y'] - self.HEIGHT - margin
            elif p1['x'] > self.WIDTH: # LEFT
                x = p1['x'] - self.WIDTH - margin
                y = p1['y'] - self.HEIGHT - margin
            elif root_w - p2['x'] > self.WIDTH: # RIGHT
                x = p2['x'] + margin
                y = p2['y'] - margin - self.HEIGHT

        return x, y
        

    def _show(self, x, y):
        self.place(width=self.WIDTH, height=self.HEIGHT, x=x, y=y)
        self.set_calendar()
        self.CLOSE = 0


    def _hide(self):
        self.place_forget()
        self.CLOSE = 1
    

    def set_calendar(self):

        self.FIRST_DATE = datetime(self.NOW.year, self.NOW.month, 1)

        control_frame = self.set_control_frame()
        date_frame = self.set_date_frame()
        
        week_days = ('Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su')
        for col, day in enumerate(week_days, 1):
            Label(date_frame, text=day).grid(column=col, row=0, sticky='NSEW')

        if self.FIRST_DATE.isoweekday() != 1:
            while self.FIRST_DATE.isoweekday() != 1:
                self.FIRST_DATE = self.FIRST_DATE - timedelta(days=1)

        for row in range(1, 7):
            end_week = False
            end_month = False
            while not end_week:
                if self.FIRST_DATE.isoweekday() == 7:
                    end_week = True

                bg = self.days_bg
                fg = self.days_fg
                border = self.days_border
                if self.NOW.month != self.FIRST_DATE.month:
                    bg = self.t_days_bg
                    fg = self.t_days_fg
                    border = self.t_days_border
                    if self.FIRST_DATE.month > self.NOW.month and self.NOW.month != 1:
                        end_month = True

                btn = Button(date_frame, text=self.FIRST_DATE.day)
                btn.grid(column=self.FIRST_DATE.isoweekday(), row=row, sticky='NSEW')
                btn.date = self.FIRST_DATE
                btn.bind("<Button-1>", self.get_date)
                self.FIRST_DATE += timedelta(days=1)
            
            if end_month:
                break

    
    def set_date_frame(self):
        if not "date_frame" in dir(self):
            control_frame = self.set_control_frame()

            date_frame = Frame(self)
            date_frame.place(width=self.WIDTH, height=self.HEIGHT-control_frame.winfo_height(), y=control_frame.winfo_height())

            for col in range(1,8):
                date_frame.columnconfigure(col, weight=1)

            for row in range(7):
                date_frame.rowconfigure(row, weight=1)

            self.date_frame = date_frame

        return self.date_frame
    
    def set_control_frame(self):
        if not "control_frame" in dir(self):
            control_frame = Frame(self)
            control_frame.place(width=self.WIDTH, height=self.HEIGHT/7)
            self.update()

            button_back = Button(control_frame, text=self.back_month_text, command=self.back_month)
            button_back.pack(fill='y', side='left', expand=0)

            month_label_text = f"{self.NOW.strftime('%B')} {self.NOW.strftime('%Y')}"
            self.month_label = Label(control_frame, text=month_label_text)
            self.month_label.pack(fill='y', side='left', expand=1)

            button_next = Button(control_frame, text=self.next_month_text, command=self.next_month)
            button_next.pack(fill='y', side='right', expand=0)

            control_frame.bind("<Button-1>", self.get_date)
            self.control_frame = control_frame

        month_label_text = f"{self.NOW.strftime('%B')} {self.NOW.strftime('%Y')}"
        self.month_label.configure(text=month_label_text)
        self.month_label.update()
        self.update()
        return self.control_frame


    def next_month(self):
        year = self.NOW.year
        month = self.NOW.month
        day = self.NOW.day

        month = month + 1 if month != 12 else 1
        year = year + 1 if month == 1 else year

        try:
            self.NOW = datetime(year, month, day)
        except:
            self.NOW = datetime(year, month, 1)
        self.set_calendar()
    

    def back_month(self):
        year = self.NOW.year
        month = self.NOW.month
        day = self.NOW.day

        month = month - 1 if month != 1 else 12
        year = year - 1 if month == 12 else year
        
        try:
            self.NOW = datetime(year, month, day)
        except:
            self.NOW = datetime(year, month, 1)
        self.set_calendar()
      

    def get_date(self, event):
        if event.widget.date:
            self.input.delete(0, "end")
            self.input.insert(0, event.widget.date.strftime(self.output_format))


    def ui_settings(self, ctrl_btn_bg="#F0F0F0", ctrl_btn_fg="#000", ctrl_lbl_bg="#F0F0F0", ctrl_lbl_fg="#000", ctrl_border=0, back_month_text="❮", next_month_text="❯", week_days_bg="#F0F0F0", week_days_fg="#000", week_border=1, days_bg="#F0F0F0", days_fg="#000", days_border=1, t_days_bg="#666", t_days_fg="#000", t_days_border=1, output_format="%Y-%m-%d"):
        self.ctrl_btn_bg = ctrl_btn_bg
        self.ctrl_btn_fg = ctrl_btn_fg
        self.ctrl_lbl_bg = ctrl_lbl_bg
        self.ctrl_lbl_fg = ctrl_lbl_fg
        self.ctrl_border = ctrl_border
        self.back_month_text = back_month_text
        self.next_month_text = next_month_text
        self.week_days_bg = week_days_bg
        self.week_days_fg = week_days_fg
        self.week_border = week_border
        self.days_bg = days_bg
        self.days_fg = days_fg
        self.days_border = days_border
        self.t_days_bg = t_days_bg
        self.t_days_fg = t_days_fg
        self.t_days_border = t_days_border
        self.output_format = output_format
        self.update()
