# Function to load Country Information from plist file
# http://www.country-files.com/cty/history.htm
def load_cty(filename):
        try:
                import plistlib
                print('Reading',filename,'...')
                with open(filename, 'rb') as f:
                        country_list = plistlib.load(f)
                return(country_list)
        except Exception as e:
                print("LOAD_CTY Error")
                print(e)
                #sys.exit(0)
                return(False)
