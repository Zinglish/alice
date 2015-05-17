from system.player import Player

class BasePlugin(object):
	
	_priority = 99
	_isInitialized = False

	def __str__(self):
		return self.name

	@classmethod
	def extend(self, obj):
		setattr(obj, func.__name__, func)

	def log_info(self, message):
		print("[" + self.name + "][Info] " + message)

	def accept_ip(self, ip, qport):
		self._alice.accept_ip(ip, qport)

	def deny_ip(self, ip, qport, message):
		self._alice.deny_ip(ip, qport, message)

	def broadcast_chat(self, message):
		self._alice.broadcast_chat(message)

	def get_plugin(self, plugin_name):
		plugin_manager = self._alice.get_plugin_manager()
		return plugin_manager.get_plugin_instance(plugin_name)

	def find_players_by_partial(self, partial_name):
		return self._alice.find_players_by_partial(partial_name)

	def propogate_event(self, event, params):
		plugin_manager = self._alice.get_plugin_manager()
		return plugin_manager.propagate_event(event, params)

	def get_players(self):
		return self._alice.players