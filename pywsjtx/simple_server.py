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

    # Function to process messages and spots from WSJT-X
    def get_spot2(self,line,verbosity=0):
        self.nsleep=0
        (pkt, addr_port) = self.rx_packet()

        line=''
        if (pkt != None):
            the_packet = pywsjtx.WSJTXPacketClassFactory.from_udp_packet(addr_port, pkt)

            if type(the_packet) == pywsjtx.HeartBeatPacket:
                print(the_packet)
            elif type(the_packet) == pywsjtx.StatusPacket:
                #print(the_packet.de_call)                  # Individual fields
                #print(the_packet)

                if self.old_status:
                    print(the_packet.status_changes(self.old_status))
                else:
                    print(the_packet)
                self.old_status=the_packet  
            
            elif type(the_packet) == pywsjtx.DecodePacket:
                #print(the_packet)
                #print('Decode:\t',the_packet.message)
                try:
                    line=the_packet.format_spot(self.old_status,'AA2IL')
                    print(line)
                    self.nsleep=1
                except:
                    line=''
                    
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
        frq = 1e-3*self.old_status.dial_frequency
        return convert_freq2band(frq,True)
        
