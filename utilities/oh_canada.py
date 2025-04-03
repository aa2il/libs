############################################################################
#
# oh_canada.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Function to determine Canadian province from callsign.
#
############################################################################
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
############################################################################

import sys
from pprint import pprint

############################################################################

VERBOSITY=0

############################################################################

# Routine to give QTH of a Canadian station
def Oh_Canada(dx_station,CQP=False):

    """
    Prefixes	Province/Territory
    --------    ------------------
    VE1 VA1	Nova Scotia
    VE2 VA2	Quebec	
    VE3 VA3	Ontario	
    VE4 VA4	Manitoba	
    VE5 VA5	Saskatchewan	
    VE6 VA6	Alberta	
    VE7 VA7	British Columbia	
    VE8	        Northwest Territories	
    VE9	        New Brunswick	
    VE0*	International Waters
    VO1	        Newfoundland
    VO2	        Labrador
    VY1	        Yukon	
    VY2	        Prince Edward Island
    VY9**	Government of Canada
    VY0	        Nunavut	
    CY0***	Sable Is.[16]	
    CY9***	St-Paul Is.[16]	

    For the CQP Prior to 2023:
    MR      Maritime provinces plus Newfoundland and Labrador (NB, NL, NS, PE)
    QC      Quebec
    ON      Ontario
    MB      Manitoba
    SK      Saskatchewan
    AB      Alberta
    BC      British Columbia
    NT 

    For the CQP after 2023:
    NS NB NL NU YT
    No TER
    
    """

    qth=''
    secs=[]
    #print('Oh Canada ... 1')
    #pprint(vars(dx_station))
    if dx_station.country=='Canada':
        prefix=dx_station.call_prefix +dx_station.call_number
        if prefix in ['VE1','VA1']:
            qth='NS'
            secs=[qth]
        elif prefix in ['VE2','VA2']:
            qth='QC'
            secs=[qth]
        elif prefix in ['VE3','VA3']:
            qth='ON'
            secs=['ONE','ONS','ONN','GH']
        elif prefix in ['VE4','VA4']:
            qth='MB'
            secs=[qth]
        elif prefix in ['VE5','VA5']:
            qth='SK'
            secs=[qth]
        elif prefix in ['VE6','VA6']:
            qth='AB'
            secs=[qth]
        elif prefix in ['VE7','VA7']:
            qth='BC'
            secs=[qth]
        elif prefix in ['VE8']:
            qth='TER'                 # Formerly NT
            secs=[qth]
        elif prefix in ['VE9']:
            qth='NB'
            secs=[qth]
        elif prefix in ['VO1','VO2']:
            qth='NL'
            secs=[qth]
        elif prefix in ['VY0']:
            qth='NU'
            secs=[qth]
        elif prefix in ['VY1']:
            if CQP:
                qth='YT'
            else:
                qth='TER'                  # Formerly YT
            secs=[qth]
        elif prefix in ['VY2']:
            qth='PE'
            secs=[qth]
        else:
            print('OH CANADA - Hmmmm',prefix)
            pprint(vars(dx_station))
            #sys.exit(0)
            
    else:
        print('OH CANADA - I dont know what I am doing here')

    #print('OH CANADA:',qth,secs)
    return qth,secs

