
######################################
### Local Area Network Module      ###
######################################
#
# API Usage:
#	arcLAN.LanSetup 			(Regenerates class configs from shelf DB)
#	arcLAN.LanRebindPort 		(Attempts to close and rebind port)
#	arcLAN.ScanNetwork 			(Scan network for nodes and add to shelf DB)
#	arcLAN.LanAddClients(IP) 	(Add client to shelf DB manually)
#	arcLAN.ThreadProvision 		(Opens node to accept provisioning from other nodes)
#	arcLAN.ThreadFindProvision 	(Initiates provisioning with other nodes)
#	arcLAN.Close 				(Close all nodes socket connections)
#	arcLAN.Sustainment 			(Threads sockets and maintains communication between nodes)
#
#######################################
### v0.01 #############################
#######################################
#
# Planned:
#	arcLAN.RDBData() 			(Push findings to RDB Module)
#	arcLAN.FriendRDBData()		(Module to assist RDBData when friendNode loses internet)
#	
#######################################

from socket import *
import socketserver
import _thread as thread
import time
import arcLog
import arcConfig
import asyncio
import threading


class Networking:
	def __init__(self, sockOBJ, ip, port, locTrackPort, locOBJ, susOBJ, susPort):
		self.sockOBJ = sockOBJ
		self.ip = ip
		self.port = port
		self.locTrackPort = locTrackPort
		self.susOBJ = susOBJ
		self.susPort = susPort
		
		@property
		def sockOBJ(self):
			return self.__sockOBJ
		def ip(self):
			return self.__ip
		def port(self):
			return self.__port
		def locTrackPort(self):
			return self.__locTrackPort
		def locOBJ(self):
			return self.__locOBJ
		def susOBJ(self):
			return self.__susOBJ
		def susPort(self):
			return self.__susPort
			
		@ip.setter
		def ip(self, ip):
			self.__ip = ip

		@port.setter
		def port(self, port):
			self.__port = port
			
		@locTrackPort.setter
		def locTrackPort(self, locTrackPort):
			self.__locTrackPort = locTrackPort
		@locOBJ.setter
		def locOBJ(self, locOBJ):
			self.__locOBJ = locOBJ
		@susOBJ.setter
		def susOBJ(self, susOBJ):
			self.__susOBJ = susOBJ
		@susPort.setter
		def susPort(self, susPort):
			self.__susPort = susPort
			

####################
####################
##### GENERAL ###### LanSetup(totalConn), LanRebindPort()
####################
####################

def LanSetup(totalConn):

# LanSetup inits networking variables for various tasks:
# Provisioning, Location Tracking, and Sustainment.
# The IP's and ports are managed through the ARC Console / database,
# the values are verified and set within arcConfig.py

# provisioning sockets:
	try:
		global provision
		provision = Networking.sockOBJ
		try:
			provision.bind((Networking.ip, int(Networking.port)))
			provision.listen(totalConn)
			arcLog.create("Provision: Sockets have been set up: {} {}".format(Networking.ip, Networking.port))
		except:
			arcLog.create("Provision: Port {} is already bound".format(Networking.port))
			#LanRebindPort(provision)
	except:
		arcLog.create("Tracking: Issue Setting up Sockets on: {} {}".format(Networking.ip, Networking.port))
		
# location tracking sockets:
	try:
		global tracking
		tracking = Networking.locOBJ
		try:
			tracking.bind((Networking.ip, int(Networking.locTrackPort)))
			tracking.listen(totalConn)
			arcLog.create("Tracking: Sockets have been set up: {} {}".format(Networking.ip, Networking.locTrackPort))
		except:
			arcLog.create("Tracking: Port {} is already bound".format(Networking.locTrackPort))
			#LanRebindPort(tracking)
	except:
		arcLog.create("Tracking: Issue Setting up Sockets on: {} {}".format(Networking.ip, Networking.locTrackPort))
		
# sustainment sockets:
	try:
		global sustainment
		sustainment = Networking.susOBJ
		try:
			sustainment.bind((Networking.ip, int(Networking.susPort)))
			sustainment.listen(totalConn)
			arcLog.create("Sustainment: Sockets have been set up: {} {}".format(Networking.ip, Networking.susPort))
		except:
			arcLog.create("Sustainment: Port {} is already bound".format(Networking.susPort))
			#LanRebindPort(tracking)
	except:
		arcLog.create("Sustainment: Issue Setting up Sockets on: {} {}".format(Networking.ip, Networking.susPort))
	
	
def LanRebindPort(conn):							# Called if port is already bound
	Networking.conn = Networking.conn + 1
	conn.close()

def CycleOff(conn):									# Cycle connection conn (provision, tracking, etc...)
	conn.close()


####################
#################### ScanNetwork(), LanAddClients(ip)
### PROVISIONING ### ProvisionServer(), FindProvision(duration)
####################
####################

# Provisioning works automatically upon being plugged into the network
# (for 10 minutes) as well as when triggered within the ARC Console API.
# A server and client is spawned. Probes are sent out while awaiting probes
# as well. A key is transferred upon connection  and verified. If it matches
# the key within the database, the node is added to the trusted client list.
# 
# Sustainment Initiates at power up, and checks the status of trusted nodes.
# If there are issues, the remaining online nodes report that to the database,
# sends email alerts, and it reflects as CRITICAL within the HALO Console.

def ScanNetwork():
	Print("IPs")								#create list of all ip's on subnet 10.0.0.255

def LanAddClients(ip):
	arcConfig.LanAddClients(ip) 				# send to shelf when found through expected data
	arcLog.create("Added Client: {}".format(ip))

def ProvisionServer():
	arcLog.create("Provision Server: Started")
	while True:
		connection, address = provision.accept()
		arcLog.create("Provision Server: Accessed from: {}".format(address))
		arcLog.create("Provision Server: Spinning Thread: {}".format(address))
		thread.start_new_thread(ProvisionServerThreaded, (connection, address))

def ProvisionServerThreaded(connection, address):
	while True:
		data = connection.recv(1024) 				# receive data when connected
		arcLog.create("Provision Thread: Server Received Data: {}".format(address))
		if arcConfig.GetKey()[0] in str(data):
			arcLog.create("Provision Thread: Key Valid from: {}".format(address))
			replyKey = "{}".format(arcConfig.GetKey())				# friendNode will verify key
			finalReplyKey = str.encode(replyKey)
			connection.send(finalReplyKey) 				# send ack with key
			arcLog.create("Provision Thread: Sending Reciprocative Key to: {}".format(address))
			LanAddClients(address) 					# add client to local db
			arcLog.create("Provision Thread: Completed Provision with {}".format(address))
			break
	arcLog.create("Provision Thread: Closing for: {}".format(address))
	connection.close()							# close connection
	thread.exit()								# exit thread

def ThreadFindProvision():
	for node in arcConfig.Nodes():
		if node not in arcConfig.GetLanClients():
			thread.start_new_thread(FindProvision(node))

def FindProvision(node):
	try:
		provision.sockOBJ.connect((node))										# setup sockets to server
	except:
		arcLog.create("No Provision Connection from {}".format(node))
		
	provision.sockOBJ.send(arcConfig.GetKey()[0])							# send key for verification
	data = Provision.sockOBJ.recv(1024)									# receive response
	if arcConfig.GetKey()[0] in str(data):									# if key in response
		arcConfig.LanAddClients(TestClient.ip)								# add server as friend
		arcLog.create("Added {} to Client's list".format(TestClient.ip))
	provision.sockOBJ.close()												# close connection
	arcLog.create("Socket Closed for: {}".format(node))



def Close(conn):
	try:
		conn.close()
		arcLog.create("Connection {} Closed on: {} {}".format(conn, Networking.ip,Networking.port))
	except:
		arcLog.create("Issue Closing Connection {} on : {} {}".format(conn, Networking.ip,Networking.port))


#########################
######################### 
### Location Tracking ### StoreValue(), LocTrackServer(), LocTrackClient()
#########################
#########################

# LocTrack entails both receiving sound alerts that meet thresholds and sharing that data
# with other nodes.The Client and Server initiate upon threshold break.
# Should update later to have enabled fulltime.

def StoreValue(address, soundData):							# Store value in shelf
	arcConfig.AddSoundData(address, soundData)

def LocTrackServer():
	arcLog.create("Location Track Server: Started")
	#connectedNodes = []
	while True:
		connection, address = tracking.accept()
		arcLog.create("LocTrack Server: Accessed from: {}".format(address))
		#if address in arcConfig.GetLanClients(): #and address not in connectedNodes:
			#connectedNodes.append(address)
		arcLog.create("LocTrack Server: Appended New Node: {}".format(address))
		thread.start_new_thread(LocTrackServerThreaded, (connection, address))
		
def LocTrackServerThreaded(connection, address):
	while True:
		arcLog.create("LocTrack Server: Spinning Thread for: {}".format(address))
		soundData = connection.recv(1024) 				# receive data when connected
		arcLog.create("Received Sound Data {} from: {}, Value: {}".format(soundData, address, soundData))
		StoreValue(address, soundData)
		arcRDB.SendTrackData()
	arcLog.create("LocTrack Thread: Closing for: {}".format(address))
	connection.close()
	thread.exit() 
	
def LocTrackClient():
	arcLog.create("LocTrack_Client: Started")
	port = 33334
	for node in arcConfig.GetLanClients():
		i = 0
		arcLog.create("LocTrack_Client: Found {} in Client List".format(node))
		thread.start_new_thread(LocTrackClientThreaded, (node, port))
		i = i + 1

def LocTrackClientThreaded(node, port):
	arcLog.create("LocTrack_Client: Spinning Thread for: {}".format(node))
	try:
		tracking.connect((node, int(Networking.locTrackPort)))		# setup sockets to server
		arcLog.create("LocTrack_Client: Connecting to: {} {}".format(node, Networking.locTrackPort))
		soundValue = "57.3db" 												# we will get this value from arcHW through function parameter
		finalSoundValue = str.encode(soundValue)
		arcLog.create("LocTrack_Client: Sending Sound Value of {} to: {} {}".format(soundValue, node, Networking.locTrackPort))
		tracking.send(finalSoundValue)							# send key for verification								# receive response
		arcLog.create("LocTrack_Client: Sound Value {} Sent: {} {}".format(soundValue, node, tracking.locTrackPort))
		thread.exit()
	except:
		arcLog.create("LocTrack_Client: Issue Connecting to: {}".format(node))
		thread.exit()


####################
####################
### SUSTAINMENT  ### SustainmentClient(), SustainmentServer()
####################
####################

# The Sustainment client is a threaded integrity checker of adjacent arc devices.
# For each node within the local db, they spin a thread to check connectivity.

def SustainmentClient():
	arcLog.create("Sustainment Client: Started")
	#threading.Timer(60.0, SustainmentClient()).start()
	#arcLog.create("Sustainment Client Scheduler: Started")
	for address in arcConfig.GetLanClients():
		arcLog.create("Sustainment: Checking {} From Client List".format(address))
		thread.start_new_thread(SustainmentClientThreaded, (sustainment, address, int(Networking.susPort)))

def SustainmentClientThreaded(sustainment, address, port):
	arcLog.create("Sustainment Client: Spinning Thread for: {} ".format(address))
	try:
		sustainment.connect((address, Networking.susPort))
		sustainment.send("OK")
		data = sustainment.recv(1024)
		if "OK" in data:
			arcLog.create("Sustainment: Check OK for node")
		if "OK" not in data:
			arcLog.create("Sustainment: Check FAILED for node")
		if not data:
			arcLog.create("Sustainment: No Data Returned")
	except:
		arcLog.create("Sustainment: Check Failed")
	
def SustainmentServer():
	arcLog.create("Sustainment Server: Started")
	#connectedNodes = []
	while True:
		connection, address = sustainment.accept()
		arcLog.create("Sustainment Server: Accessed from: {}".format(address))
		#if address in arcConfig.GetLanClients(): #and address not in connectedNodes:
			#connectedNodes.append(address)
		#arcLog.create("Sustainment Server: Appended New Node: {}".format(address))
		thread.start_new_thread(LocTrackServerThreaded, (connection, address))

def SustainmentServerThreaded(connection, address):
	arcLog.create("Sustainment Server: Spinning Thread for: {} ".format(address))
	while True:
		arcLog.create("Sustainment Server: Spinning Thread for: {}".format(address))
		data = connection.recv(1024) 				# receive data when connected
		arcLog.create("Sustainment Server: Received ACK Check from: {}".format(address))
		if "OK" in data:
			arcLog.create("Sustainment: Check OK for node")
		if "OK" not in data:
			arcLog.create("Sustainment: Check FAILED for node")
		if not data:
			arcLog.create("Sustainment: No Data Returned")
		sustainment.send("OK")
	arcLog.create("Sustainment Server: Thread Closing for: {}".format(address))
	connection.close()
	thread.exit() 


if __name__ == '__main__':
	
	#db = arcConfig.OpenShelf()

	Networking.sockOBJ = socket(AF_INET, SOCK_STREAM) #stay
	Networking.locOBJ = socket(AF_INET, SOCK_STREAM) #stay
	Networking.susOBJ = socket(AF_INET, SOCK_STREAM) #stay


########################################
########################################
### Temporary External Testing  ########
########################################
########################################

# These would already be set in production through the configuration
# within Arc HALO.

	arcConfig.SetKey("arc009922!%&$#33")
	arcConfig.SetLANIP('127.0.0.1', '33333', '33334', '33336')
	arcConfig.LanAddClients('10.0.0.3')
	arcConfig.LanAddClients('127.0.0.1')
	Networking.ip = arcConfig.GetLANIP()[0]
	Networking.port = arcConfig.GetLANIP()[1]
	Networking.locTrackPort = arcConfig.GetLANIP()[2]
	Networking.susPort = arcConfig.GetLANIP()[3]
	LanSetup(99)

###################
#### Components ###
###################
###### thread #####
###################

# Enable this for Provision Server:
	thread3 = threading.Thread(target=ProvisionServer)
	thread3.daemon = True
	thread3.start()

# Enable this for LocTrack Testing:
	thread2 = threading.Thread(target=LocTrackServer)
	thread2.daemon = True
	thread2.start()

# although socket may already be bounded for self device
	thread1 = threading.Thread(target=LocTrackClient)
	thread1.daemon = True
	thread1.start()

# Enable this for sustainment testing
	thread0 = threading.Thread(target=SustainmentServer)
	thread0.daemon = True
	thread0.start()

	thread4 = threading.Thread(target=SustainmentClient)
	thread4.daemon = True
	thread4.start()

	while True:
		a = "a"


#--
#asyncProvision = asyncio.get_event_loop()
#asyncProvision.run_until_complete(ThreadProvision())
#---
#asyncLocTrack = asyncio.get_event_loop()
#asyncLocTrack.run_until_complete(LocTrackServer())
#---
#asyncSustainment = asyncio.get_event_loop()
#asyncSustainment.run_until_complete(SustainmentCheck())
#---
#try:
	#asyncProvision.run_forever()
	#asyncLocTrack.run_forever()
	#asyncSustainment.run_forever()
	
#finally:
	#asyncProvision.close()
	#asyncLocTrack.close()
	#asyncSustainment.close()


#ThreadProvision() # complete
#LocTrackServer() # needs testing
#SustainmentCheck() # in progess






