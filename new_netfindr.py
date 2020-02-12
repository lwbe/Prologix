import random
import struct


NETFINDER_SERVER_PORT  = 3040

NF_IDENTIFY                     =  0
NF_IDENTIFY_REPLY               =  1
NF_ASSIGNMENT                   =  2
NF_ASSIGNMENT_REPLY             =  3
NF_FLASH_ERASE                  =  4
NF_FLASH_ERASE_REPLY            =  5
NF_BLOCK_SIZE                   =  6
NF_BLOCK_SIZE_REPLY             =  7
NF_BLOCK_WRITE                  =  8
NF_BLOCK_WRITE_REPLY            =  9
NF_VERIFY                       = 10
NF_VERIFY_REPLY                 = 11
NF_REBOOT                       = 12
NF_SET_ETHERNET_ADDRESS         = 13
NF_SET_ETHERNET_ADDRESS_REPLY   = 14
NF_TEST                         = 15
NF_TEST_REPLY                   = 16

NF_SUCCESS                      = 0
NF_CRC_MISMATCH                 = 1
NF_INVALID_MEMORY_TYPE          = 2
NF_INVALID_SIZE                 = 3
NF_INVALID_IP_TYPE              = 4

NF_MAGIC                        = 0x5A

NF_IP_DYNAMIC                   = 0
NF_IP_STATIC                    = 1

NF_ALERT_OK                     = 0x00
NF_ALERT_WARN                   = 0x01
NF_ALERT_ERROR                  = 0xFF

NF_MODE_BOOTLOADER              = 0
NF_MODE_APPLICATION             = 1

NF_MEMORY_FLASH                 = 0
NF_MEMORY_EEPROM                = 1

NF_REBOOT_CALL_BOOTLOADER       = 0
NF_REBOOT_RESET                 = 1


HEADER_FMT                      = "!2cH6s2x"
IDENTIFY_FMT                    = HEADER_FMT
IDENTIFY_REPLY_FMT              = "!H6c4s4s4s4s4s4s32s"
ASSIGNMENT_FMT                  = "!3xc4s4s4s32x"
ASSIGNMENT_REPLY_FMT            = "!c3x"
FLASH_ERASE_FMT                 = HEADER_FMT
FLASH_ERASE_REPLY_FMT           = HEADER_FMT
BLOCK_SIZE_FMT                  = HEADER_FMT
BLOCK_SIZE_REPLY_FMT            = "!H2x"
BLOCK_WRITE_FMT                 = "!cxHI"
BLOCK_WRITE_REPLY_FMT           = "!c3x"
VERIFY_FMT                      = HEADER_FMT
VERIFY_REPLY_FMT                = "!c3x"
REBOOT_FMT                      = "!c3x"
SET_ETHERNET_ADDRESS_FMT        = "!6s2x"
SET_ETHERNET_ADDRESS_REPLY_FMT  = HEADER_FMT
TEST_FMT                        = HEADER_FMT
TEST_REPLY_FMT                  = "!32s"

MAX_ATTEMPTS                    = 10
MAX_TIMEOUT                     = 0.5

#-----------------------------------------------------------------------------
def MkHeader(id, seq, eth_addr):
    return struct.pack(
        HEADER_FMT,
        bytes(chr(NF_MAGIC),"utf-8"),
        bytes(chr(id),"utf-8"),
        seq,
        bytes(eth_addr,"utf-8")
        );    
#-----------------------------------------------------------------------------
def MkIdentify(seq):
    return MkHeader(NF_IDENTIFY, seq, '\xFF\xFF\xFF\xFF\xFF\xFF')

#-----------------------------------------------------------------------------
def UnMkIdentifyReply(msg):
    hdrlen = struct.calcsize(HEADER_FMT)
    
    d = UnMkHeader(msg[0:hdrlen])
    
    params = struct.unpack(
        IDENTIFY_REPLY_FMT,
        msg[hdrlen:]
        ); 
        
    d['uptime_days'] = params[0]
    d['uptime_hrs'] = ord(params[1])
    d['uptime_min'] = ord(params[2])
    d['uptime_secs'] = ord(params[3])
    d['mode'] = ord(params[4])
    d['alert'] = ord(params[5])
    d['ip_type'] = ord(params[6])
    d['ip_addr'] = params[7]
    d['ip_netmask'] = params[8]
    d['ip_gw'] = params[9]
    d['app_ver'] = params[10]
    d['boot_ver'] = params[11]
    d['hw_ver'] = params[12]
    d['name'] = params[13]
    return d

#-----------------------------------------------------------------------------
def UnMkHeader(msg):
    params = struct.unpack(
        HEADER_FMT,
        msg
        ); 
        
    d = {}
    d['magic'] = ord(params[0])
    d['id'] = ord(params[1])
    d['sequence'] = params[2]
    d['eth_addr'] = params[3]
    return d
#-----------------------------------------------------------------------------
def FormatEthAddr(a):
    return ":".join(["%02X" % i for i in a])  

#-----------------------------------------------------------------------------
def PrintDetails(d):

    print()
    print("Ethernet Address: %s " %  FormatEthAddr(d['eth_addr']))
    print("Hardware: %s Bootloader: %s  Application: %s"  %  (socket.inet_ntoa(d['hw_ver']),
                                                              socket.inet_ntoa(d['boot_ver']),
                                                              socket.inet_ntoa(d['app_ver'])))
    #print "Uptime:", d['uptime_days'], 'days', d['uptime_hrs'], 'hours', d['uptime_min'], 'minutes', d['uptime_secs'], 'seconds'
    #if d['ip_type'] == NF_IP_STATIC:
    #    print "Static IP"
    #elif d['ip_type'] == NF_IP_DYNAMIC:
    #    print "Dynamic IP"
    #else: 
    #    print "Unknown IP type"
    print("IP Address: %s Mask :%s Gateway: %s" % (socket.inet_ntoa(d['ip_addr']),
                                                   socket.inet_ntoa(d['ip_netmask']),
                                                   socket.inet_ntoa(d['ip_gw'])))
    #print "Mode:",
    #if d['mode'] == NF_MODE_BOOTLOADER:
    #    print 'Bootloader'
    #elif d['mode'] == NF_MODE_APPLICATION:
    #    print 'Application'
    #else:
    #    print 'Unknown'

#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------


import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
port = 0
s.bind(("10.220.0.2", port))
port = s.getsockname()[1]

r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
r.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
r.setblocking(1)
r.settimeout(0.500)
r.bind(('', port))

seq = random.randint(1, 65535)
msg = MkIdentify(seq)

s.sendto(msg, ('<broadcast>', NETFINDER_SERVER_PORT))
reply=r.recv(256)
d=UnMkIdentifyReply(reply)
PrintDetails(d)


