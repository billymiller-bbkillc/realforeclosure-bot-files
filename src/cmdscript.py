import sys
from itertools import islice
from subprocess import Popen, PIPE, STDOUT
from textwrap import dedent
from threading import Thread
import tkinter as tk
from queue import Queue, Empty
import time

def iter_except(function, exception):
    """Works like builtin 2-argument `iter()`, but stops on `exception`."""
    try:
        while True:
            yield function()
    except exception:
        return

class DisplaySubprocessOutputDemo:
    
    def __init__(self, root, script_fn=None, command=None, callback=None):
        self.root = root
        self.callback = callback

        # start dummy subprocess to generate some output
        if script_fn:
            with open(script_fn, "r", encoding="utf-8") as file:
                command = file.read()
        command_ar = command.split(" ")
        self.process = Popen(command_ar, stderr=STDOUT, stdin=PIPE, stdout=PIPE)

        # launch thread to read the subprocess output
        #   (put the subprocess output into the queue in a background thread,
        #    get output from the queue in the GUI thread.
        #    Output chain: process.readline -> queue -> label)
        q = Queue(maxsize=1024)  # limit output buffering (may stall subprocess)
        t = Thread(target=self.reader_thread, args=[q, self.process])
        t.daemon = True # close pipe if GUI process exits
        t.start()

        # show subprocess' stdout in GUI
        self.update(q) # start update loop

    def reader_thread(self, q, process):
        """Read subprocess output and put it into the queue."""
        for pipe in [process.stdout]:
            while True:
                line = pipe.readline()
                print(line)
                if not line:
                    break
                q.put(line)
        q.put(None)

    def update(self, q):
        """Update GUI with items from the queue."""
        for line in iter_except(q.get_nowait, Empty): # display all content
            print("line", line)
            if line == None:
                self.quit()
                return
            else:
                self.callback(line)
                break # display no more than one line per 40 milliseconds
        self.root.after(40, self.update, q) # schedule next update

    def quit(self):
        self.process.kill() # exit subprocess if GUI is closed (zombie!)

