import sys
import threading
import time
from bluepy.btle import Scanner, DefaultDelegate, Peripheral, BTLEException

devices = []
start = 0
isConnected = False
isWaiting = True

## The values returned are (type, value, traceback)
tp, val, tb = sys.exc_info()

## Handle the notifications from HC-08
class MyDelegate(DefaultDelegate):
    def __init__(self, params, i):
        DefaultDelegate.__init__(self)
        self.name = params
	self.i = i
        print "received data from "+self.name

    def handleNotification(self, cHandle, data):
        print "echo seq=%d"%self.i +" "+data
        global start
        global isConnected
        if self.i == 0:
            if start == 0:
                start = time.time()

        total = time.time() - start
	print total
	self.i += 1
	if((data == "dismiss") | (total > 100)):
	    isConnected = False
        
class connect(threading.Thread):
    def __init__(self, lock, seq, threadname, dev):
        super(connect, self).__init__(name = threadname)
	self.dev = dev
	self.lock = lock
	self.seq = seq

    def run(self):
	global devices
	print "seq%d" % self.seq + " start connecting to " + self.name
	try:
	    addr = self.dev.addr	
	    p = Peripheral(addr)
	    i = 0
	    p.setDelegate(MyDelegate(self.name, i))
            print "seq%d"%self.seq+" connected to " + self.name
            service = p.getServiceByUUID("0000ffe0-0000-1000-8000-00805f9b34fb")
	    ch = service.getCharacteristics()
	    for char in ch:
	        if char.uuid == "0000ffe0-0000-1000-8000-00805f9b34fb":
		    break

	    send_lock = threading.Lock()
	    BleSend(send_lock, self.name, char).start()
            BleReceive(send_lock, self.name, p).start()

	except:
            print "seq%d"%self.seq+" error occurred"
	    BTLEException.DISCONNECTED
	    reset()
	    print "exception occurred"
	    info = sys.exc_info()  
   	    print info[0],":",info[1],":",info[2]

class BleSend(threading.Thread):
    def __init__(self, lock, threadname, char):
	super(BleSend, self).__init__(name = threadname)
	self.char = char

    def run(self):
	global isConnected
	isRunning = True
        print "Welcome to Echo Server"

	while isRunning:
	    time.sleep(10)
            if isConnected:
		try:
	            self.char.write("WelcometoEchoServer")
		    print "10secs are passed"
		except:
		    isRunning = False
		    print "exception occurred"
		    info = sys.exc_info()
		    print info[0],":",info[1],":",info[2]
	    else:
	        isRunning = False
		reset()

class BleReceive(threading.Thread):
    def __init__(self, lock, threadname, p):
	super(BleReceive, self).__init__(name = threadname)
    	self.p = p
	
    def run(self):
        global isConnected
        while isConnected:
	    try:
	        self.p.waitForNotifications(10.0)
	    except:
		print "exception occurred"
		info = sys.exe_info()
		print info[0],":",info[1],":",info[2]

        self.p.disconnect()
	print "disconnected"

class BleScan(threading.Thread):
    def __init__(self, lock, threadname):
	super(BleScan, self).__init__(name = threadname)
        self.lock = lock         
        self.i = 0
    
    def run(self):
	global devices
        global isConnected
	connect_lock = threading.Lock()
	while True:
            self.i += 1
	    print "seq%d"%self.i + " BLEScanning"
	    print "current state:"
	    print threading.enumerate()
	    
	    if not isConnected:
	        devicelist = Scanner().scan(3.0)
		for dev in devicelist: 
	            device_name = dev.getValueText(9)
     		    if "HSCC_BLE_" in str(device_name):
		        if dev not in devices:
			    isConnected = True
			    devices.append(dev)
			    connect(connect_lock, self.i, device_name, dev).start()		        
            else:
		time.sleep(5)
		print "Scan Again"		    
	
def reset():
    global devices 
    global start
    global isConnected
    global isWaiting
    devices = []
    start = 0
    isConnected = False
    isWaiting = True
    print "reset done"

scan_lock = threading.Lock()
BleScan(scan_lock, "BLEScan").start() 

