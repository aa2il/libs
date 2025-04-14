############################################################################
#
# error_handler.py - Rev 1.0
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
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
import inspect

############################################################################

def stack_trace(txt):
    print('\n',txt,'\n')
    summary = traceback.StackSummary.extract( 
        traceback.walk_stack(None) 
    ) 
    print(''.join(summary.format()))
    print('--- EXIT---')
    sys.exit(0)

    
def error_trap(msg,trace=False):

    print('\n*** Trapped Exception ***',msg)
    
    exc_type, exc_value, exc_traceback = sys.exc_info()
    if exc_type!=None:
        print(exc_type.__name__,': ',exc_value)
    
        fname=exc_traceback.tb_frame.f_code.co_filename
        lineno=exc_traceback.tb_lineno
        func=exc_traceback.tb_frame.f_code.co_name
        print('\nFile:\t',fname,' at line ',lineno,' in ',func)
        line = linecache.getline(fname,lineno)
        print('Code:',line,flush=True)
    else:
        print('\n\tERROR_TRAP: Well thats weird - no exc_info - now what???',flush=True)

    if trace:
        traceback.print_exc()

    if exc_type!=None and exc_type.__name__=='SystemExit':
        print('--- EXITING ---')
        raise

    if exc_type!=None:
        return [exc_type.__name__,exc_value]
    else:
        return [None,None]
    
############################################################################

def whoami():
    #parent=inspect.stack()[0].function  # This just return whoami - not useful - need to look at rackback stuff
    name=inspect.stack()[1].function
    #name = '\n *+*+*+*+*+*+*+*+*+*+*  '+ name +' ***'
    #return name
    #txt = '*** '+parent+'-->'+name+' ***'
    txt = name
    return txt

############################################################################

