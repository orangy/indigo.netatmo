#!/usr/bin/env python2.5
# Filename: berkinet.py

import indigo
import re
import socket
from urllib2 import urlopen

########################################
def setLogLevel(self, pluginDisplayName, logLevel):
	if logLevel == "0":
		logLevel = 0
		debug = False
	elif logLevel == "1":
		logLevel = 1
		debug = False
	elif logLevel == "2":
		logLevel = 2
		debug = False
	elif logLevel == "3":
		logLevel = 3
		debug = True
	elif logLevel == "4":
		logLevel = 4
		debug = True
	else:
		logLevel = 1
		debug = False
		
	logLevelList = ['None', 'Normal', 'Verbose', 'Debug', 'Intense Debug']
	if logLevel > 0: indigo.server.log ("Log level preferences are set to \"%s\"." % \
		logLevelList[logLevel], type=pluginDisplayName)
	
	return (logLevel, debug)
	
########################################
def versionCheck(self, pluginDisplayName, logLevel, pluginId, pluginVersion):	
	if logLevel > 1: self.debugLog(u"versionCheck() called")
	myVersion = str(pluginVersion)
	theUrl = 'http://orangy.github.io/indigo.netatmo/version.html'
	if logLevel > 2: indigo.server.log('url:%s' % theUrl, type=pluginDisplayName)
	socket.setdefaulttimeout(3)
	try:
		f = urlopen(theUrl)
		latestVersion = str(f.read()).rstrip('\n')
		if myVersion < latestVersion:
			self.errorLog(u"You are running v%s. A newer version, v%s is available." \
				% (myVersion, latestVersion))
		else:
			if logLevel > 0: indigo.server.log(u'Your plugin version, v%s, is current.' % \
				myVersion, type=self.pluginDisplayName)
	except:
		self.errorLog(u"Unable to reach the version server.")
		
