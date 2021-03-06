import string
from ConfigParser import ConfigParser

from system.plugin_manager       import PluginManager
from system.wonderland_interface import WonderlandInterface
from system.rabbithole_interface import RabbitholeInterface

from system.event    import EventParser
from system.function import Function

from system.player import Player

import globals

class Alice:
	def __init__(self):
		self._alice_config  = ConfigParser()
		self._plugin_config = ConfigParser()
		self._alice_config.read('config.ini')
		self._plugin_config.read('plugin_config.ini')

		self._players = []
		self._server_initialized = False
		self._max_players = 0

		rabbit_hole_path = "/tmp/rabbithole.ipc.28960"

		# Create the connection to the rabbit hole
		self._rabbithole = RabbitholeInterface()
		self._rabbithole.connect(rabbit_hole_path)

		# Since we will be parsing events more often than not, it's better to
		# declare a general event parser to save on speed and memory.
		self._event_parser = EventParser()

		self._plugin_manager = PluginManager(self)
		self._plugin_manager.load_plugins()
		self._plugin_manager.prioritize_plugins()
		self._plugin_manager.initialize_plugins()

		if self.get_max_players() > 0:
			self._server_initialized = True
			self._initialize()

		self._run()

	##
	# Called when the CoD server has been initialized correctly.
	# 
	# initialize:
	##
	def _initialize(self):
		self.build_players()
		self._plugin_manager.propagate_on_server_init()

	##
	# Contains the main loop/thread.
	# 
	# run:
	##
	def _run(self):
		while True:
			# Attempt to recieve an entire packet
			rx = self._rabbithole.recv()

			if rx:
				self._analyze_packet(rx)
			else:
				break
		
		self._rabbithole.close()

	##
	# Analyzes the packet coming in on the main and decides what to do with it.
	# 
	# analyze_packet:
	# 	@param pkt [str] - Packet
	##
	def _analyze_packet(self, pkt):
		# If event, then parse the event and pass it on to the event executor
		if pkt[0] == 'E':
			if globals.DEBUG:
				print("Recieved event: ")
				print("\t" + ":".join("{:02x}".format(ord(c)) for c in pkt))

			event = self._event_parser.parse(pkt)
			self._exec_event(event)

	##
	# Depending on what event this is, it's executed accordingly.
	# 
	# exec_event:
	# 	@param event [Event] - Describe
	##
	def _exec_event(self, event):
		event_name = event.get_name()
		plugin_man = self._plugin_manager

		if event_name   == 'INIT':
			if not self._server_initialized:
				self._server_initialized = True
				self._initialize()
		elif event_name == 'CHAT':
			slot_id = event.get_arg(0)
			message = event.get_arg(1)
			player  = self._players[slot_id]
			
			plugin_man.propagate_on_player_chat(player, message)
		elif event_name == 'CHANGENAME':
			pass
		elif event_name == 'JOIN':
			slot_id     = event.get_arg(0)
			player_ip   = event.get_arg(1)
			player_guid = event.get_arg(2)
			player_info = event.get_arg(3).split('\\')

			# Parse the player's name out
			player_name = ""
			for i in range(len(player_info)):
				if player_info[i] == 'name':
					player_name = player_info[i + 1]

			self._players[slot_id] = Player(self)
			self._players[slot_id].init(slot_id, player_ip, player_guid, player_name)

			plugin_man.propagate_on_player_join(self._players[slot_id])
		elif event_name == 'JOINREQ':
			ip    = event.get_arg(0)
			qport = event.get_arg(1)

			plugin_man.propagate_on_join_req(ip, qport)
		elif event_name == 'DC':
			slot_id = event.get_arg(0)
			player  = self._players[slot_id]

			plugin_man.propagate_on_player_dc(player)

			self._players[slot_id] = None

	##
	# Builds the list of players by using the player data obtained from the
	# CoD server.
	# 
	# TODO: If this is called twice, the list gets fucked up...this needs
	# 		to be fixed.
	# 
	# build_players:
	##
	def build_players(self):
		for i in range(self.get_max_players()):
			self._players.append(None)

		data = string.split(self.get_player_data(), '\n')
		for line in data:
			if line != '':
				player_data = string.split(line, '\\\\')

				player_id   = int(player_data[0])
				player_ip   = player_data[1]
				player_guid = player_data[2]
				player_name = player_data[3]

				self._players[player_id] = Player(self)
				player = self._players[player_id]

				player.init(player_id, player_ip, player_guid, player_name)


	#=======================================================================================#
	# Gtors and Stors                                                                       #
	#=======================================================================================#
	
	def get_plugin_manager(self):
		return self._plugin_manager


	#=======================================================================================#
	# Void Function Calls                                                                   #
	#=======================================================================================#

	##
	# Accepts a Limbo'd IP address.
	#
	# accept_ip:
	# 	@param ip    [str] - IP of the address that's in Limbo
	# 	@param qport [int] - Quake port
	##
	def accept_ip(self, ip, qport):
		void_func = Function('LIMBOACCEPT', ip, qport)
		self._rabbithole.send_void_func(void_func)

	##
	# Denies an IP in Limbo. Shows a reason why the IP was denied to the user.
	# 
	# deny_ip:
	# 	@param ip      [str] - IP of the address that's in Limbo
	# 	@param qport   [int] - Quake port
	# 	@param message [str] - Reason why the IP was denied, this is shown to the
	# 						   user.
	##
	def deny_ip(self, ip, qport, message):
		void_func = Function('LIMBODENY', ip, qport, message)
		self._rabbithole.send_void_func(void_func)

	##
	# Sends a chat message to all players who are connected.
	#
	# broadcast_chat:
	# 	@param message [str] - Chat message to broadcast
	##
	def broadcast_chat(self, message):
		void_func = Function('BCASTPRINTF', 0, message)
		self._rabbithole.send_void_func(void_func)

	##
	# Sends a chat message to a secific player.
	# 
	# tell:
	# 	@param player_id [int] - The player ID that is to recieve the message
	# 	@param message   [str] - The message to send to the player
	##
	def tell(self, player_id, message):
		print("Tell: " + str(player_id) + " " + message)
		void_func = Function('CHATPRINTF', 0, player_id, message)
		self._rabbithole.send_void_func(void_func)


	#=======================================================================================#
	# Return Function Calls                                                                 #
	#=======================================================================================#

	##
	# Gets the maximum amount of players that can join the server.
	# 
	# get_max_players:
	# 	@return [int]
	##
	def get_max_players(self):
		if self._max_players == 0:
			return_func = Function('GETSLOTCOUNT', 1)
			self._max_players = self._rabbithole.send_return_func(return_func)

		return self._max_players

	##
	# Gets all the player data from the server, acts similar to the 'status'
	# RCON call but easier to parse and only contains player data.
	# 
	# get_player_data:
	# 	@return [str] - Formatted player data
	##
	def get_player_data(self):
		return_func = Function('PLAYERDATA', 1)
		rtn = self._rabbithole.send_return_func(return_func)
		
		return rtn


	#=======================================================================================#
	# Player Search Functions                                                               #
	#=======================================================================================#

	##
	# Finds player(s) based on a partial input search. Search is not
	# case sensitive.
	# 
	# find_players_by_partial:
	# 	@param  partial_name [str]  - Partial name.
	# 	@return              [list] - A list of Player instance objects.
	##
	def find_players_by_partial(self, partial_name):
		rtn = []
		l_partial_name = partial_name.lower()

		for player in self._players:
			if player != None:
				l_player_name = player.get_clean_name().lower()
				if l_player_name.find(l_partial_name) > -1:
					rtn.append(player)

		return rtn
