#! /usr/bin/python3
############################################################################################
#
# scp.py - Rev 1.0
# Copyright (C) 2022 by Joseph B. Attili, aa2il AT arrl DOT net
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
    def __init__(self,fname='~/Python/data/MASTER.SCP'):

        print('Loading Super Check Partial Database from',fname,'...')
        with open(os.path.expanduser(fname)) as f:
            scp = f.readlines()

        self.calls=[s.strip() for s in scp if '#' not in s]
        print('No. calls in SCP database=',len(self.calls))
        #print(calls[0],calls[-1])

    def match(self,call,MAX_DX=1):

        call=call.upper()
        matches=[]
        dist=[]
        for c in self.calls:
            dx= Levenshtein.distance(call,c) 
            if dx<=MAX_DX:
                dist.append(dx)
                matches.append(c)

        matches = [x for _, x in sorted(zip(dist,matches))]
                
        return matches
        
############################################################################################

# Test program
if __name__ == '__main__':
    SCP=SUPER_CHECK_PARTIAL()
    call = input("Enter a call:\n")
    if len(call)==0:
        call='aa2il'
    print('Calls matching',call,':',SCP.match(call,MAX_DX=max(1,call.count('?'))) )


