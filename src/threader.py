
from threading import Thread, Event, Lock
from queue import Queue
import math
import more_itertools


class Threader : 

	def runThreads(fn, argss, thread_count=1):
		threads_chunked = more_itertools.chunked(list(argss), thread_count)
		for threads_chunk in threads_chunked:
			Threader.runParallel(fn, threads_chunk)

	def runChunks(fn, argss, per_chunk=5):
		thread_count = math.ceil(len(list(argss)) / per_chunk)
		Threader.runThreads(fn, argss, thread_count)

	def runParallel(fn, argss):
		threads = []
		for args in argss:
			thread = Thread(target=fn, args=(args,))
			threads.append(thread)
		for thread in threads:
			thread.start()
		for thread in threads:
			thread.join()

class ThreadSafeCallstack :

	def __init__(self):
		self.callstack = Queue()

	def runCallstack(self, key=None):
		while not self.callstack.empty():
			value = self.callstack.get()
			value[0](*value[1], **value[2])

	def schedule(self, fn, *args, **kwargs):
		self.callstack.put([fn, args, kwargs])
		self.runCallstack()

class Scheduler :

	callstack = None
	thread_count = 1

	def __init__(self, thread_count=1):
		self.setThreadCount(thread_count)
		self.callstack = Queue()

	def getThreadCount(self):
		return self.thread_count

	def setThreadCount(self, thread_count):
		self.thread_count = thread_count

	def runCallstack(self, force_run=False):
		if self.callstack.qsize() >= self.thread_count or force_run:
			threads = []
			while not self.callstack.empty():
				value = self.callstack.get()
				thread = Thread(target=value[0], args=value[1], kwargs=value[2])
				threads.append(thread)
			for thread in threads:
				thread.start()
			for thread in threads:
				thread.join()

	def complete(self):
		self.runCallstack(force_run=True)

	def schedule(self, fn, *args, **kwargs):
		self.callstack.put([fn, args, kwargs])
		self.runCallstack()
