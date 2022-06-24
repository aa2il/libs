#!/usr/bin/python
# Filename: cty.py

def load_cty(filename):
        """ Load Country Information from plist file (http://www.country-files.com/cty/history.htm)"""
        try:
                import plistlib
                print('Reading',filename,'...')
                #country_list = plistlib.readPlist(filename)     # Orig but now depricated
                with open(filename, 'rb') as f:
                        country_list = plistlib.load(f)
                return(country_list)
        except Exception as e:
                print("LOAD_CTY Error")
                print(e)
                #sys.exit(0)
                return(False)
                
# End of cty.py
