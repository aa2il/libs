# It looks like the original came from   https://github.com/bmo/py-wsjtx.git
# There is some other interesting stuff there, e.g. interfacing with
# N1MM logger.
#
# In WSJTX parlance, the 'network server' is a program external to the wsjtx.exe program that handles packets emitted by wsjtx
#
# TODO: handle multicast groups.
#
# see dump_wsjtx_packets.py example for some simple usage
#
import socket
import struct
import pywsjtx
import logging
import ipaddress
from rig_io.util import convert_freq2band
import re
import datetime

class SimpleServer(object):
    logger = logging.getLogger()
    MAX_BUFFER_SIZE = pywsjtx.GenericWSJTXPacket.MAXIMUM_NETWORK_MESSAGE_SIZE
    DEFAULT_UDP_PORT = 2237
    #
    #
    def __init__(self, ip_address='127.0.0.1', udp_port=DEFAULT_UDP_PORT, **kwargs):
        self.timeout = None
        self.verbose = kwargs.get("verbose",False)
        self.old_status=None
        self.prev_time=None
        self.prev_band=None

        if kwargs.get("timeout") is not None:
            self.timeout = kwargs.get("timeout")

        the_address = ipaddress.ip_address(ip_address)
        if not the_address.is_multicast:
            self.sock = socket.socket(socket.AF_INET,  # Internet
                                 socket.SOCK_DGRAM)  # UDP

            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.bind((ip_address, int(udp_port)))
        else:
            self.multicast_setup(ip_address, udp_port)

        if self.timeout is not None:
            self.sock.settimeout(self.timeout)

    def multicast_setup(self, group, port=''):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', port))
        mreq = struct.pack("4sl", socket.inet_aton(group), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    def rx_packet(self):
        try:
            pkt, addr_port = self.sock.recvfrom(self.MAX_BUFFER_SIZE)  # buffer size is 1024 bytes
            return(pkt, addr_port)
        except socket.timeout:
            if self.verbose:
                logging.debug("rx_packet: socket.timeout")
            return (None, None)

    def send_packet(self, addr_port, pkt):
        bytes_sent = self.sock.sendto(pkt,addr_port)
        self.logger.debug("send_packet: Bytes sent {} ".format(bytes_sent))

    def demo_run(self):
        while True:
            (pkt, addr_port) = self.rx_packet()
            if (pkt != None):
                the_packet = pywsjtx.WSJTXPacketClassFactory.from_udp_packet(addr_port, pkt)
                print(the_packet)

    # Routine to highlight a particualr callsign in the WSJT decoding window - TYPE 13
    def highlight_spot(self,callsign,fg,bg):
        #color_pkt = pywsjtx.HighlightCallsignPacket.Builder(self.wsjtx_id, callsign,
        #                                                    pywsjtx.QCOLOR.Uncolor(),
        #                                                    pywsjtx.QCOLOR.Red(),
        #                                                    True)

        color_pkt = pywsjtx.HighlightCallsignPacket.Builder(self.wsjtx_id, callsign,
                                                            pywsjtx.QCOLOR.COLORS(bg),
                                                            pywsjtx.QCOLOR.COLORS(fg),
                                                            True)
        self.send_packet(self.addr_port, color_pkt)

    # Routine to configure some of the WSJT parameters - TYPE 15
    def configure_wsjt(self,NewMode='',RxDF=-1,DxCall='',DxGrid=''):
        # At startup, this doesn't work so just trap error
        try:
            config_pkt = pywsjtx.ConfigurePacket.Builder(self.wsjtx_id,
                                                         Mode=NewMode,
                                                         RXDF=int(RxDF),
                                                         DXCall=DxCall, DXGrid=DxGrid)
            self.send_packet(self.addr_port, config_pkt)
        except:
            pass


    # Function to process messages and spots from WSJT-X
    def get_spot2(self,line,verbosity=0):
        self.nsleep=0
        (pkt, addr_port) = self.rx_packet()

        line=''
        if (pkt != None):
            the_packet = pywsjtx.WSJTXPacketClassFactory.from_udp_packet(addr_port, pkt)

            if type(the_packet) == pywsjtx.HeartBeatPacket:
                print('\n',the_packet)
                utc = datetime.datetime.utcnow()
                try:
                    print('time=',utc,'\tfrq =',self.old_status.dial_frequency)
                except:
                    pass

            elif type(the_packet) == pywsjtx.StatusPacket:
                if False:
                    print('================= Get_Spot2: Status Packet:')
                    print(the_packet)
                    #print(the_packet.de_call)                  # Individual fields
                
                if self.old_status:
                    print(the_packet.status_changes(self.old_status))
                else:
                    print('New Status:\t',the_packet)
                self.old_status=the_packet
            
            elif type(the_packet) == pywsjtx.DecodePacket:
                print(the_packet)
                time=the_packet.time
                band=self.old_status.dial_frequency
                print('GetSpot2: time=',time,self.prev_time,'\tband=',band,self.prev_band)
                if self.prev_time and (self.prev_time==time) and (self.prev_band!=band):
                    #print('Get Spot2: Band change during interval - discarding packet')
                    #return ''
                    print('Get Spot2: Band change during interval - Fixing packet')
                    FREQ=self.prev_band
                else:
                    self.prev_time=time
                    self.prev_band=band
                    FREQ=0
            
                #print('Decode:\t',the_packet.message)
                try:
                    line=the_packet.format_spot(self.old_status,'AA2IL',FREQ)
                    print('Decode:\t',line)
                    self.nsleep=1
                except:
                    line=''

                # Save these if we need to respond to this packet,e.g. highlight color
                self.addr_port = addr_port
                self.wsjtx_id  = the_packet.wsjtx_id
                    
                # This is how to highlight call signs
                if the_packet.message:
                    m = re.match(r"^CQ\s+(\S+)\s+", the_packet.message)
                else:
                    m=None
                if m and False:
                    print("Callsign {}".format(m.group(1)))
                    callsign = m.group(1)

                    print('&&&&&&&&&&&&&&&&&&&&&&&&&&&& ID=',the_packet.wsjtx_id)

                    color_pkt = pywsjtx.HighlightCallsignPacket.Builder(the_packet.wsjtx_id, callsign,
                                                                        pywsjtx.QCOLOR.White(),
                                                                        pywsjtx.QCOLOR.Red(),
                                                                        True)

                    #normal_pkt = pywsjtx.HighlightCallsignPacket.Builder(the_packet.wsjtx_id, callsign,
                    #                                                     pywsjtx.QCOLOR.Uncolor(),
                    #                                                     pywsjtx.QCOLOR.Uncolor(),
                    #                                                     True)
                    self.send_packet(addr_port, color_pkt)

                

            elif type(the_packet) == pywsjtx.QSOLoggedPacket and False:
                print(the_packet)
                #print('HEEEEEYYYYYYYYY!   5555555555555555')
                #print('Logger:\t',the_packet.adif)
                #line=the_packet.adif
                    
            elif type(the_packet) == pywsjtx.LoggedADIFPacket:
                print(the_packet)
                #print('HEEEEEYYYYYYYYY!      12121212121212')
                #print('Logger:\t',the_packet.adif_text)
                line=the_packet.adif_text
                    
            else:
                print('*** Need handler ***')
                print(the_packet)

        else:
            #print('Nothing heard')
            pass

        return line

    # Dummy function for backward compatatibilty - the spot is already formatted
    def convert_spot(self,spot):
        if not spot:
            return ''
        else:
            return spot

    def last_band(self):
        try:
            frq = 1e-3*self.old_status.dial_frequency
        except:
            frq=14074.
        return convert_freq2band(frq,True)

    def wsjt_status(self):
        try:
            frq = 1e-3*self.old_status.dial_frequency
        except:
            frq=14074.
        band=convert_freq2band(frq,True)            
        return [frq,band]
        
