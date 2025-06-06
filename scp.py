#! /home/joea/miniconda3/envs/aa2il/bin/python -u
#
# NEW: /home/joea/miniconda3/envs/aa2il/bin/python -u
# OLD: /usr/bin/python3 -u 
############################################################################################
#
# scp.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Class to make use of Super Check Partial Database
#
# Notes:
#       pip3 install python-Levenshtein
#
############################################################################################
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
############################################################################################

import os
import sys
import Levenshtein
from fileio import parse_file_name
import glob 
from load_history import *
from dx import Station,load_cty_info

############################################################################################

class SUPER_CHECK_PARTIAL:
    def __init__(self,fname=None):

        # Check for valid file name
        if fname==None:
            fname = os.path.expanduser('~/Python/data/MASTER.SCP')
        elif '*' in fname:
            # Expand wildcards and only keep the most recent call history file
            fnames = os.path.expanduser(fname)
            print('SCP_INIT: fname=',fname)
            print('SCP_INIT: fnames=',fnames)
            files=[]
            for f in glob.glob( fnames ):
                print('f=',f)
                files.append(f)
                if len(files)==0:
                    print('file=',files)
                    print('SCP_INIT - No files found matching',fname)
                    sys.exit(0)
            files.sort()
            print('SCP_INIT: files=',files)
            fname=files[-1]

        p,n,ext=parse_file_name(fname)
        print(fname,p,n,ext,len(p))
        if len(p)==0 and not os.path.isfile(fname):
            fname = os.path.expanduser('~/Python/history/data/'+fname)
                
        if not os.path.isfile(fname):
            print('SCP INIT: File not found',fname)
            self.calls=[]
            return

        print('SCP INIT: Loading Super Check Partial Database from',fname,'...')
        if ext=='.SCP':
            with open(fname) as f:
                scp = f.readlines()
            #self.calls=[s.strip() for s in scp if '#' not in s]
            self.calls=[]
            for s in scp:
                if '#' not in s:
                    call = s.strip()

                    # There might be a problem with too many spot_proc loggers - need to fix this
                    if '/' in call and True:
                        dx = Station(call)
                        call = dx.homecall
                    
                    self.calls.append(call)
            self.MAX_DX=1            
        else:
            scp,fname9 = load_history(fname)
            #print(scp)
            if False:
                self.calls=list(scp.keys())
            else:
                self.calls=[]
                for call in scp.keys():
                    if '/' in call:
                        dx = Station(call)
                        self.calls.append(dx.homecall)
                    else:
                        self.calls.append(call)
            self.MAX_DX=1

        self.calls = list( set(self.calls) )
        #print('calls=',self.calls)
        print('No. calls in SCP database=',len(self.calls))
        print(self.calls[0],self.calls[-1])
        #sys.exit(0)

        
    # Function to find matches
    def match(self,call,MAX_DX=None,VERBOSITY=0):

        if not MAX_DX:
            MAX_DX=self.MAX_DX

        call = ''.join(call.upper().split())
        if len(call)==0:
            return [],[]

        # Look through SCP list and find possible matches
        matches1=[]
        matches2=[]
        dist1=[]
        dist2=[]
        n=len(call)
        for c in self.calls:
            dx= Levenshtein.distance(call,c)
            
            # First chars match OR distance less than 1
            if call==c[:n] or dx<=MAX_DX:
                dist1.append(dx)
                matches1.append(c)

            # Just in case nothing matches, keep list of dist less than 2
            if dx<=MAX_DX+1:
                dist2.append(dx)
                matches2.append(c)

        # Sort matches by distance from call
        if len(matches1)>0:
            matches = [x for _, x in sorted(zip(dist1,matches1))]
        else:
            matches = [x for _, x in sorted(zip(dist2,matches2))]

        # Put calls that match the first chars to the front of the list
        if False:
            
            for i in range(len(matches)):
                if call in matches[i]:
                    m=matches.pop(i)
                    matches.insert(0,m)
                    
        elif True:

            matches1=[]
            matches2=[]
            for m in matches:
                if call in m:
                    matches1.append(m)
                else:
                    matches2.append(m)

            if VERBOSITY>0:
                print('SCP: matches1=',matches1)
            matches=matches1+matches2
                    
        if VERBOSITY>0:
            print('SCP: call=',call,' - ',matches,'\ndist',dist,'\n',matches1)
        return matches,matches1
        
############################################################################################

# Test program
if __name__ == '__main__':

    load_cty_info()
    SCP_FNAME=None
    #SCP_FNAME='~/Python/history/data/K1USNSST-*.txt'

    SCP=SUPER_CHECK_PARTIAL(SCP_FNAME)
    call = input("\nEnter a call:\n")
    if len(call)==0:
        call='aa2il'
    matches=SCP.match(call,MAX_DX=max(1,call.count('?')))
    print('\nCalls matching',call,':',matches)

    sys.exit(0)

