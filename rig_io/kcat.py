############################################################################################
#
# kcat.py
# Copyright (C) 2021-5 by Joseph B. Attili, joe DOT aa2il AT gmail DOT com
#
# Stubs for kcat socket io to help get Bill started
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

from .dummy_io import *
import socket

############################################################################################

VERBOSITY=0

############################################################################################

# Stubs for Kachina 505
class kcat_connect(no_connect):

    def __init__(self,host=None,port=None,tag=''):
        no_connect.__init__(self)
        self.active     = True
        self.rig_type   = 'KCAT'
        self.rig_type1  = 'KCAT'
        self.rig_type2  = 'KC505'

        if host:
            self.host = host
        else:
            self.host = '127.0.0.1'       # Everything will run on localhost - change if over lan

        if port:
            self.port = port
        else:
            self.port = 7365             # Bill, put the proper port here

        # Open socket to server
        print('KCAT CONNECT: Opening socket to',self.host,' on port',self.port,' ...')
        self.s = socket.socket()
        self.s.connect((self.host, self.port))   
        self.s.settimeout(0.1) # 100 ms timeout

        # Read rig freq & mode
        frq = self.get_freq()
        print('KCAT CONNECT: Rig Freq=',frq)
        mode = self.get_mode()
        print('KCAT CONNECT: Rig mode=',mode)
        
    def send_cmd(self, xml_cmd):
        try:
            self.s.sendall(xml_cmd.encode("utf-8"))
            data = self.s.recv(1024)
            response = data.decode("utf-8").strip()
            print(f"[send_cmd] Sent: {xml_cmd}, Received: {response}")
            if response.startswith("<RESPONSE>") and response.endswith("</RESPONSE>"):
                return response[len("<RESPONSE>"):-len("</RESPONSE>")]
            return response  # return raw if not wrapped
        except Exception as e:
            print(f"[send_cmd] Error sending {xml_cmd}: {e}")
            return None
    
    def get_mode(self,VFO='A'):
        return self.send_cmd("<CMD>get_mode</CMD>")
        
    def set_mode(self, mode, VFO='A', Filter=None):
        return self.send_cmd(f"<SET>set_mode={mode}</SET>")
        
    def get_freq(self,VFO='A'):
        return float(self.send_cmd("<CMD>get_frequency</CMD>"))

    def set_freq(self, freq, VFO='A'):
        return self.send_cmd(f"<SET>set_freq={freq}</SET>")
    
