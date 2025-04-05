#! /usr/bin/python3 -u
################################################################################
#
# JBA - this is very slow bx .plist file is huge (~14Mb)
# There has to be a better way!

# plist = Apple property list, can be binary also
# Binary is much faster to load!!!!
# To convert XML file to BINARY:
#          sudo apt install libplist-util
#          plistutil -i cty.plist -o cty.bin
#
################################################################################

#import asyncio
#import aiofiles
import sys
from utilities import error_trap

# Function to load Country Information from plist file
# http://www.country-files.com/cty/history.htm
def load_cty(filename):
#async def load_cty(filename):
        try:
                import plistlib
                print('LOAD CTY: Reading',filename,'...')
                #sys.exit(0)
                with open(filename, 'rb') as f:
                        country_list = plistlib.load(f)
                #async with aiofiles.open(filename, 'rb') as f:
                #         country_list = await plistlib.load(f)
                return(country_list)
        except:
                error_trap('Problem loading CTY file: fname='+filename,1)
                #sys.exit(0)
                return(False)


################################################################################

# Test program
if __name__ == '__main__':
        import os
        import sys
        from utilities import find_resource_file

        fname=find_resource_file('cty.plist')
        fname=find_resource_file('cty.bin')
        print('fname=',fname)
        if os.path.isfile(fname):
                dxcc = load_cty(fname)              #Load Country File

        #print('dxcc=',dxcc)
        #print('type=',type(dxcc))
        #print('keys=',dxcc.keys())
        print('len=',len(dxcc.keys()))
        print('K=',dxcc['K'])
        print('N=',dxcc['N'])
        print('W=',dxcc['W'])

        sys.exit(0)

        # Let's play with this cty.dat file
        # pip install ctyparser
        # Info is similar but not quite the same

        import ctyparser

        fname2=find_resource_file('cty.dat')
        print('fname2=',fname2)
        cty=ctyparser.BigCty()
        cty.import_dat(fname2)
        #print('version=',cty.formatted_version)
        #cty.dump('cty.json')

        dxcc2=cty._data
        #print('dxcc2=',dxcc2)
        #print('type2=',type(dxcc2))
        #print('keys2=',dxcc2.keys())
        print('len2=',len(dxcc2.keys()))
        print('K=',dxcc2['K'])
        print('N=',dxcc2['N'])
        print('W=',dxcc2['W'])


