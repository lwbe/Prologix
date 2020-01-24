import os,serial,socket
import logging
logging.basicConfig(level=logging.DEBUG)
SERIAL_TIMEOUT=0.5

class Prologix_Device():
    def __init__(self,
                 type="USB",
                 serial_number=None,
                 baudrate=9600,
                 timeout=SERIAL_TIMEOUT):        
        
        if type.lower()=="usb":
            if serial:
                port = self.find_dev(serial_number)
                if port == None:
                    raise Exception("No port found for serial_number %s !!\nABORTING " % serial_number)
                
                self.serial_dev = serial.Serial(port,baudrate=baudrate,timeout=timeout)
                
            else:
                raise Exception("Serial number not given")
        else:
            raise Exception("type %s not implemented yet" % type)
        
    def find_dev(self,sn):
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

    def send(self,msg):

        if type(msg) == bytes:
            s_msg = msg
        else:
            s_msg=msg.encode()
        s_msg += b'\n'
        
        logging.info("Sending Data %s",repr(str(s_msg)))
        self.serial_dev.write(s_msg)
        logging.info("==> %s " % repr(self.serial_dev.read(10000)))
        
    def read(self):
        logging.info("Reading Data")
        self.send(b"++read")
        return self.serial_dev.read(10000)
    
    def read(self):
        logging.info("Reading Data with auto 1")
        self.send(b"++read")
        return self.serial_dev.read(10000)
    
    def raw_read(self):
        logging.info("Reading Raw Data")
        return self.serial_dev.read(100)

    def check_command(self,cmd):
        usage="""
Available commands are:

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
        
        list_of_available_commands="++addr,++auto,++clr,++eoi,++eos,++eot_enable,++eot_char,++ifc,++loc,++lon,++mode,++read,++read_tmo_ms,++rst,++savecfg,++spoll,++srq,++status,++trg,++ver,++help".split(',')

        if cmd.startswith("++"):
            if (cmd in list_of_available_commands) or cmd.lower()[0]=="q":
                return True
            else:
                print(usage)
                return False
        return True

    
if __name__=="__main__":


           
    default_sn="PXG9ASAT"
    running=True
    p = Prologix_Device(serial_number=default_sn)

    try_good=False
    comment="""if try_good:
        pass
        p.send("++mode 0")
        p.send("++addr 0")
        p.send("++mode 1")
        p.send("++mode")
        p.send("++mode 1")
        p.send("++auto 0")
        p.send("++eoi  1")
        p.send("++eos  1")
        p.send("++eot_enable 0")
        p.send("++eot_char 10")
        p.send("++addr 12")
        p.send("ALLF?\r\n++read")
        p.send("ALLF?\r\n")
        
    else:
        pass
        p.send("++mode 0")
        p.send("++addr 0")
        p.send("++mode 1")
        p.send("++mode")
        p.send("++eot_enable 1")
        p.send("++eot_char 10")
        p.send("++auto 0")
        #p.send("++eoi  1")
        #p.send("++eos  1")
        #p.send("++addr 12")
        p.send("ALLF?\r\n++auto 1")
        p.send("++auto 0")
"""
    p.send("++addr")
    p.send("++auto")
    p.send("++eoi")
    p.send("++rst")
    p.send("++ver")
    p.send("++eos")
    p.send("++eot_enable")
    p.send("++eot_char")
    p.send("++mode")
    p.send("++status")
    p.send("++ver")

    
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
        

