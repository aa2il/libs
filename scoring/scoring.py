############################################################################################
#
# default.py - Rev 1.0
# Copyright (C) 2025 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Scoring Routine Selector
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

import sys
from .default import CONTEST_SCORING
from .sst import SST_SCORING
from .naqp import NAQP_SCORING

############################################################################################

# Routine to select proper scoring routine for a given contest
def Select_Scoring(P):
    print('SELECT SCORING: contest_mode=',P.CONTEST_MODE,'\tContest Name=',P.CONTEST_NAME)
    #sys.exit(0)
    sc=None
    if P.CONTEST_MODE:
        if P.CONTEST_NAME in ['SST']:
            sc=SST_SCORING(P,'SST')
        elif P.CONTEST_NAME in ['NAQP']:
            sc=NAQP_SCORING(P)
        else:
            sc=CONTEST_SCORING(P,'Default')
    else:
        sc=CONTEST_SCORING(P,'Default')
        
    return sc
