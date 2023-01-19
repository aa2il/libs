#! /usr/bin/python3
############################################################################################
#
# scp.py - Rev 1.0
# Copyright (C) 2022-3 by Joseph B. Attili, aa2il AT arrl DOT net
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

############################################################################################

class SUPER_CHECK_PARTIAL:
    def __init__(self,fname=None):

        # Check for valid file name
        if fname==None:
            fname=os.path.expanduser('~/Python/data/MASTER.SCP')
            if not os.path.isfile(fname):
                fname='MASTER.SCP'
        if not os.path.isfile(fname):
            self.calls=[]
            return

        print('Loading Super Check Partial Database from',fname,'...')
        with open(fname) as f:
            scp = f.readlines()

        self.calls=[s.strip() for s in scp if '#' not in s]
        print('No. calls in SCP database=',len(self.calls))
        #print(calls[0],calls[-1])

    def match(self,call,MAX_DX=1,VERBOSITY=0):

        call=call.upper()

        # Look through SCP list and find possible matches
        matches=[]
        dist=[]
        for c in self.calls:
            dx= Levenshtein.distance(call,c) 
            if dx<=MAX_DX:
                dist.append(dx)
                matches.append(c)

        # Sort matches by distance from call
        matches = [x for _, x in sorted(zip(dist,matches))]

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
    SCP=SUPER_CHECK_PARTIAL()
    call = input("\nEnter a call:\n")
    if len(call)==0:
        call='aa2il'
    matches=SCP.match(call,MAX_DX=max(1,call.count('?')))
    print('\nCalls matching',call,':',matches)

    sys.exit(0)

