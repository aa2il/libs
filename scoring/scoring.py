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
from .sst     import SST_SCORING
from .mst     import MST_SCORING
from .cwt     import CWT_SCORING
from .cqp     import CQP_SCORING
from .fd      import FIELD_DAY_SCORING
from .cwopen  import CWOPEN_SCORING
from .iaru    import IARU_HF_SCORING
from .naqp    import NAQP_SCORING
from .vhf     import VHF_SCORING
from .arrl_ss import ARRL_SS_SCORING
from .rttyru  import ARRL_RTTY_RU_SCORING

############################################################################################

# Routine to select proper scoring routine for a given contest
def Select_Scoring(P):
    print('SELECT SCORING: contest_mode=',P.CONTEST_MODE,'\tContest Name=',P.CONTEST_NAME)
    #sys.exit(0)
    sc=None
    if P.CONTEST_MODE:
        if P.CONTEST_NAME in ['SST']:
            sc=SST_SCORING(P,'SST')
        elif P.CONTEST_NAME in ['MST']:
            sc=MST_SCORING(P)
        elif P.CONTEST_NAME in ['CWT']:
            sc=CWT_SCORING(P)
        elif P.CONTEST_NAME in ['CQP']:
            sc=CQP_SCORING(P)
        elif P.CONTEST_NAME in ['SS']:
            sc=ARRL_SS_SCORING(P)
        elif P.CONTEST_NAME in ['FD']:
            sc=FIELD_DAY_SCORING(P)
        elif P.CONTEST_NAME in ['CWOPEN']:
            sc=CWOPEN_SCORING(P)
        elif P.CONTEST_NAME in ['IARU']:
            sc=IARU_HF_SCORING(P)
        elif P.CONTEST_NAME in ['NAQP']:
            sc=NAQP_SCORING(P,'NAQP')
        elif P.CONTEST_NAME in ['VHF']:
            sc=VHF_SCORING(P)
        elif P.CONTEST_NAME in ['WPX']:
            sc=WPX_SCORING(P)
        elif P.CONTEST_NAME in ['ARRL-RTTY','ARRL-10','CQ-160']:
            sc=ARRL_RTTY_RU_SCORING(P,P.CONTEST_NAME)
        else:
            sc=CONTEST_SCORING(P,'Default')
    else:
        sc=CONTEST_SCORING(P,'Default')
        
    return sc
