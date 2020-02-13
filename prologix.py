import os,sys
import logging


dbg_lvl = {
    "critical" : logging.CRITICAL,
    "error"    : logging.ERROR,
    "warning"  : logging.WARNING,
    "info"     : logging.INFO,
    "debug"    : logging.DEBUG
    }
    

logging.basicConfig(level=logging.DEBUG)
SERIAL_TIMEOUT=0.5

help_usage = """
Prologix commands are:

   ++addr 0-30 [96-126]  -- specify GPIB address 
   ++addr                -- query GPIB address 
   ++auto 0|1            -- enable (1) or disable (0) read-after-write 
   ++auto                -- query read-after-write setting 
   ++clr                 -- issue device clear 
   ++eoi 0|1             -- enable (1) or disable (0) EOI with last byte 
   ++eoi                 -- query eoi setting 
   ++eos 0|1|2|3         -- EOS terminator - 0:CR+LF, 1:CR, 2:LF, 3:None 
   ++eos                 -- query eos setting 
   ++eot_enable 0|1      -- enable (1) or disable (0) appending eot_char on EOI 
   ++eot_enable          -- query eot_enable setting 
   ++eot_char <char>     -- specify eot character in decimal 
   ++eot_char            -- query eot_char character 
   ++ifc                 -- issue interface clear 
   ++loc                 -- set device to local 
   ++lon                 -- enable (1) or disable (0) listen only mode 
   ++mode 0|1            -- set mode - 0:DEVICE, 1:CONTROLLER 
   ++mode                -- query current mode 
   ++read [eoi|<char>]   -- read until EOI, <char>, or timeout 
   ++read_tmo_ms 1-3000  -- set read timeout in millisec
   ++read_tmo_ms         -- query timeout 
   ++rst                 -- reset controller 
   ++savecfg 0|1         -- enable (1) or disable (0) saving configuration to EPROM 
   ++savecfg             -- query savecfg setting 
   ++spoll               -- serial poll currently addressed device 
   ++spoll 0-30 [96-126] -- serial poll device at specified address 
   ++srq                 -- query SRQ status 
   ++status 0-255        -- specify serial poll status byte 
   ++status              -- query serial poll status byte 
   ++trg                 -- issue device trigger 
   ++ver                 -- query controller version 
   ++help                -- display this help
"""

# helper function that convert string to bytes.
#-----------------------------------------------------------------------------------------------------------
def to_bytes(a):
    if type(a) == bytes:
        return a
    return a.encode()

# a class for debuging it only provides write and read function
#===========================================================================================================
class dummy_device():
#-----------------------------------------------------------------------------------------------------------
    def write(self,msg):
        print(msg)
#-----------------------------------------------------------------------------------------------------------
    def read(self,n):
        print("should return something but in debug mode nothing")


# the class to talk to the prologix
#===========================================================================================================
class Prologix_Device():
#-----------------------------------------------------------------------------------------------------------
    def __init__(self,
                 dev="usb",
                 serial_number=None,
                 ip=None,
                 baudrate=9600,
                 timeout=SERIAL_TIMEOUT,
                 gpib_eot="\r\n",
                 debug_level="critical"):

        if dbg_lvl.get(debug_level):
            logging.getLogger().setLevel(dbg_lvl.get(debug_level))
        else:
            raise Exception("debug level %s not understood should be one of" % ( debug_level,
                                                                                 ", ".join(dbg_lvl.keys())))
        
        self.gpib_eot = to_bytes(gpib_eot)
        
        if dev.lower() == "dummy":
            self.device = dummy_device()
            
        elif dev.lower() == "usb":
            import serial
            if serial_number:
                port = self.find_dev(serial_number)
                if port == None:
                    raise Exception("No port found for serial_number %s !!\nABORTING " % serial_number)
                logging.debug("Debug serial device serial_number %s (port %s)" % (serial_number,port))
                logging.debug("                    baudrate %s type(%s) " % (baudrate,type(baudrate)))
                logging.debug("                    timeout %s type(%s)" % (timeout,type(timeout)))
                logging.debug("                    gpib_eot %s" % (repr(self.gpib_eot)))

                self.device = serial.Serial(port,baudrate=baudrate,timeout=timeout)
            else:
                raise Exception("Serial number not given")
        else:
            raise Exception("type %s not implemented yet" % type)
#-----------------------------------------------------------------------------------------------------------
    def find_dev(self,sn):
        """
        return the path in /dev for the serial number sn or None if not found
        """

        # Note we can get a lot of information with this
        # 'apply_usb_info',
        # 'description',
        # 'device',
        # 'device_path',
        # 'hwid',
        # 'interface',
        # 'location',
        # 'manufacturer',
        # 'name',
        # 'pid',
        # 'product',
        # 'read_line',
        # 'serial_number',
        # 'subsystem',
        # 'usb_description',
        # 'usb_device_path',
        # 'usb_info',
        # 'usb_interface_path',
        # 'vid']

        from serial.tools import list_ports
        for p in list_ports.comports():
            if p.serial_number==sn:
                return p.device
        return None
#-----------------------------------------------------------------------------------------------------------
    def find_dev_obsolote(self,sn):
        """
        very rough method to get the /dev/ attached to a serial_number
        """
        
        path = "/dev/serial/by-id"
        for r, d, f in os.walk(path):
            for i in f:
                if sn in i and os.path.islink(os.path.join(path,i)):
                    logging.info("Found device %s for serial number %s" %
                        (os.path.realpath(os.path.join(path,i)),sn))
                    
                    return os.path.realpath(os.path.join(path,i))
        return None
#-----------------------------------------------------------------------------------------------------------
    def config(self,mode=1,auto=0,eoi=1,eos=1,eot_enable=0,eot_char=10):
        # see https://github.com/rambo/python-scpi/blob/master/scpi/transports/gpib/prologix.py for some values
        self.send("++mode %d" % mode)
        self.send("++auto %d" % auto)
        self.send("++eoi %d" % eoi)
        self.send("++eos %d" % eos)
        self.send("++eot_enable %d" % eot_enable)
        self.send("++eot_char %d" % eot_char)
#-----------------------------------------------------------------------------------------------------------
    def scan_gpib_addresses(self):
        for a in range(31):
            r = self.query("++spoll %d" % a).decode()
            if r:
                print("found something at gpib_address %d" % a)            
#-----------------------------------------------------------------------------------------------------------
    def send(self,msg):
        """
        send the message to the prologix
        """
        s_msg = to_bytes(msg)

        full_command = b""
        for c in s_msg.split(b";"):
            if self.check_command(c): #c.startswith(b"++"):
                full_command += c+b"\n"
                logging.debug("prologix command %s" % repr(c+b"\n"))
            else:
                full_command += c+self.gpib_eot
                logging.debug("GPIB command %s" % repr(c+self.gpib_eot))


        logging.info("Sending Data %s",repr(full_command))
        self.device.write(full_command)
#-----------------------------------------------------------------------------------------------------------
    def read(self):
        logging.info("Reading Data")
        self.send(b"++read")
        return self.device.read(1000)
#-----------------------------------------------------------------------------------------------------------
    def query(self,msg):
        self.send(msg)
        logging.info("Reading Raw Data")
        ret_val = self.device.read(1000)
        logging.info("==> %s " % repr(ret_val))
        return ret_val
#-----------------------------------------------------------------------------------------------------------
    def check_command(self,cmd):

        list_of_available_commands=[ b"++addr",
                                     b"++auto",
                                     b"++clr",
                                     b"++eoi",
                                     b"++eos",
                                     b"++eot_enable",
                                     b"++eot_char",
                                     b"++ifc",
                                     b"++loc",
                                     b"++lon",
                                     b"++mode",
                                     b"++read",
                                     b"++read_tmo_ms",
                                     b"++rst",
                                     b"++savecfg",
                                     b"++spoll",
                                     b"++srq",
                                     b"++status",
                                     b"++trg",
                                     b"++ver",
                                     b"++help"]

        # we try to see if you have a prology command or not. It starts by ++ and should be one of the list above
        if cmd.startswith(b"++"):
            is_prologix_command = False
            for i in list_of_available_commands:
                if cmd.lower().startswith(i):
                    is_prologix_command=True
                    break
            if is_prologix_command:
                return True
            else:
                print("%s unknown !! "% cmd)
                print(help_usage)
                return False
        return True
#===========================================================================================================


if __name__=="__main__":


    import argparse

    parser = argparse.ArgumentParser()
    
    parser.add_argument("device", choices=["usb", "tcp", "dummy","prologix_cmd"],
                    help="define the  type of connection to the prologix or print prologix command")
    
    parser.add_argument("-s", "--serial_number",help="Serial number (only for serial)",default=None)
    parser.add_argument("-b","--baudrate", help="baudrate (only for serial)",default=9600)
    parser.add_argument("-i", "--ip",help="IP address of the device (only for tcp)",default=None)
    
    parser.add_argument("-t","--timeout", help="timeout",default=SERIAL_TIMEOUT)
    debug_choices=["critical","error","warning","info","debug"]
    parser.add_argument("-d","--debug_level", help="set debug level",choices=debug_choices,default="critical")

    #parser.add_argument("--gpib_eot",help="",default= "\r\n")
    
    args = parser.parse_args()
        
    if args.device == "prologix_cmd":
        print(help_usage)
        sys.exit(0)
    elif args.device == "dummy":
        p = Prologix_Device(dev="dummy",debug_level=args.debug_level)
    elif args.device == "usb":
        if args.serial_number == None:
            print("usb need a serial_number!!")
            parser.print_help(sys.stderr)
            sys.exit(0)
        p = Prologix_Device(dev="usb",
                            serial_number=args.serial_number,
                            baudrate=int(args.baudrate),
                            timeout=float(args.timeout),
                            debug_level=args.debug_level)
    else:
        print("type %s not implemented yet" % args.device)
        sys.exit(0)

    p.config()
    print("Scanning gpib adresses ..")
    p.scan_gpib_addresses()
    print("... Done")
                   
    interact_usage="""
You can now send, query and read command from the prologix\n\tNote that each command should be preceded by a letter indicating the  type of command
    (q) for query
    (s) for send
    (r) for read (in this case r is the only character on the line

examples:
    q++addr   will query the prologix to find it's adress. It is equivalent to
    s++addr
    r

to Quit the program type Q
"""
    
    print(interact_usage)
    # the loop that will interact with the device
    is_running = True
    while is_running:
        cmd = input("cmd > ")
        if cmd=="Q":
            is_running = False
        elif cmd != "":
            if cmd[0]=="q":
                print(p.query(cmd[1:]))
            elif cmd[0]=="s":
                p.send(cmd[1:])
            elif cmd=="r":
                print(p.read())
            else:
                print("unknown first character %s can only be (s)end, (q)uery, (r)ead" % cmd[0])
            
    print("Bye !!")
    
    #default_sn="PXG9ASAT"
    #running=True
    #p = Prologix_Device(serial_number=default_sn)

    #try_good=False
    comment="""if try_good:
        pass
        p.send("++addr 12")
        p.send("ALLF?\r\n++read")
        p.send("ALLF?\r\n")
        
    else:
        pass
        #p.send("++addr 12")
        p.send("ALLF?\r\n++auto 1")
        p.send("++auto 0")
"""
    #p.send("++addr")
    #p.send("++auto")
    #p.send("++eoi")
    #p.send("++rst")
    #p.send("++ver")
    #p.send("++eos")
    #p.send("++eot_enable")
    #p.send("++eot_char")
    #p.send("++mode")
    #p.send("++status")
    #p.send("++ver")

    
    #p.send("++help")
    
    
    #p.send("*idn?\r\n")
    #p.read()
    #p.send("ALLF?\r\n")
    #p.read()
    #p.send("ALLF?\r\n++read")
    #print("yup")
    #p.send("ALLF?\r\n++auto 1")


        


    running = False
    while running:
        cmd= raw_input("type a command ")
        if cmd=="q":
            running=False
        else:
            c = p.check_command(cmd)
            if c:
                p.send(cmd)
            else:
                print(c)
        

