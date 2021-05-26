################################################################################

# DX SPOTS - J.B.Attili - ?

# Module to process DX spots
#
# I'm not sure where the original for this came from.
# If you recognize this code, please email me so I can give proper attribution.

################################################################################

class DxSpot(object):
    def __init__(self,s):
        self.spotter=""
        self.freq=0
        self.dxcall=""
        self.utc=""
        self.gridloc=""
        self.comment=""

        self.parse_spot(s);

    def parse_spot(self,s):
        a=s.split(":")
        self.spotter=a[0][6:]

        b=a[1].strip().split()
        self.freq=float(b[0])
        del b[0]

        self.dxcall=b[0]
        del b[0]

        if b[-1]=="Z":
            self.utc=b[-1]
            self.gridloc=""
        else:
            self.utc=b[-2]
            self.gridloc=b[-1]
            del b[-2]
        del b[-1]

        self.comment=' '.join(b)


