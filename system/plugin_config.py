import ConfigParser

class PluginConfig():
	def __init__(self, config, plugin):
		self._config = config
		self._plugin = plugin

	##
	# Gets a value from the plugin config, if no value exists that
	# that key then it returns the default entry.
	#
	# get:
	##
	def get(self, key, default=None):
		try:
			v = self._config.get(self._plugin.name, key, 0)

			if v == None:
				return default

			return v
		except ConfigParser.NoSectionError:
			return default