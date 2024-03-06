############################################################################
#
# error_handler.py - Rev 1.0
# Copyright (C) 2024 by Joseph B. Attili, aa2il AT arrl DOT net
#
# Graceful Error handling
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
import traceback
import linecache

############################################################################

def error_trap(msg,trace=False):

    print('\n*** Trapped Exception ***',msg)
    
    exc_type, exc_value, exc_traceback = sys.exc_info()
    print(exc_type.__name__,': ',exc_value)
    
    fname=exc_traceback.tb_frame.f_code.co_filename
    lineno=exc_traceback.tb_lineno
    func=exc_traceback.tb_frame.f_code.co_name
    print('\nFile:\t',fname,' at line ',lineno,' in ',func)
    line = linecache.getline(fname,lineno)
    print('Code:',line)

    if trace:
        traceback.print_exc()
    
