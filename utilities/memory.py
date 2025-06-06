#! /usr/bin/python3 -u
################################################################################
#
# memory.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# A simple memory monitor to diagnos leaks and memory piggies.
#
################################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
################################################################################

import sys
import os
import psutil
import time

################################################################################

VERBOSITY=0

################################################################################

class Memory_Monitor:
    def __init__(self,fname=None):

        # Init memory monitoing stuff
        self.process = psutil.Process(os.getpid())
        self.t0      = time.time()
        if fname:
            if sys.platform == "linux" or sys.platform == "linux2":
                # linux
                pass
            elif sys.platform == "win32":
                # Windows...
                #fname=os.path.expanduser( fname.replace('/tmp','%temp%') )
                fname=os.path.expanduser( fname.replace('/tmp','~/Python/tmp') )
            elif sys.platform == "darwin":
                # OS X
                print('MEMORY MONITOR: No support for Mac OS')
                sys.exit(0)
            
            self.LOG = open(fname,'w') 
            self.LOG.write('#Time (sec),Mem Usage (Mb)\t'+str(self.process)+'\n')
            self.LOG.flush()
        else:
            self.LOG = None

    def take_snapshot(self,VERBOSITY=0):
        mem = self.process.memory_info().rss / 1024**2
        dt = time.time() - self.t0
        if VERBOSITY>0:
            print('MEMORY USAGE:',dt/60.,'min.\t',mem,'Mb\n')
        if self.LOG:
            self.LOG.write('%8.1f,%8.1f\n' % (dt,mem))
            self.LOG.flush()        



# inner psutil function
def process_memory():
    process = psutil.Process(os.getpid())
    mem_info = process.memory_info()
    return mem_info.rss

# decorator function
def memory_profile(func):
    def wrapper(*args, **kwargs):

        mem_before = process_memory()
        result = func(*args, **kwargs)
        mem_after = process_memory()
        print("{}:consumed memory: {:,}".format(
            func.__name__,
            mem_before, mem_after, mem_after - mem_before))

        return result
    return wrapper

