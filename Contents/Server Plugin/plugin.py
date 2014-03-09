#! /usr/bin/env python
# -*- coding: utf-8 -*-
####################
# Copyright (c) 2013, Richard Perlman All rights reserved.
# with special thanks to philippelt@users.sourceforge.net
# Public domain source code
#

################################################################################
# Imports
################################################################################
from berkinet import setLogLevel, versionCheck
import lnetatmo
import socket
import __builtin__
import indigo  # Not necessary, but removes lots of lint errors

################################################################################
# Globals
################################################################################


class Plugin(indigo.PluginBase):
    ########################################
    # Class properties
    ########################################
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs)

        (self.logLevel, self.debug) = setLogLevel(self, pluginDisplayName, pluginPrefs.get("showDebugInfo1", "1"))

        self.userId = pluginPrefs.get("userId", "None")
        self.userPass = pluginPrefs.get("userPass", "None")
        self.netatmoUnits = pluginPrefs.get("netatmoUnits", "None")
        self.netatmoFreq = int(pluginPrefs.get("netatmoFreq", 5))
        self.netatmoTimeout = int(pluginPrefs.get("netatmoTimeout", 100))
        self.stopThread = False
        self.runNetatmo = True
        self.timerDict = {}
        __builtin__.pluginDisplayName = pluginDisplayName
        __builtin__.logLevel = self.logLevel

    ########################################
    def __del__(self):
        indigo.PluginBase.__del__(self)

    ########################################
    def startup(self):
        if self.logLevel > 1: indigo.server.log(u'Entered: Funct startup' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        versionCheck(self, self.pluginDisplayName, self.logLevel, self.pluginId, self.pluginVersion)


  ########################################
    def readNetatmo(self):
        if self.logLevel > 1: indigo.server.log(u'Entered: Funct readNetatmo' ,  type=self.pluginDisplayName + ' Debug', isError=False)

        if self.userId == "None":
            self.errorLog("Plugin config is missing user credentials.")
            return

        authorization = lnetatmo.ClientAuth(self.userId, self.userPass)

        if authorization == 'error':
            indigo.server.log(u'Server error. Will retry in %s seconds' % (self.netatmoFreq*60),  type=self.pluginDisplayName, isError=True)
            return
        else:
            prId = "com.berkinet.Netatmo"
            netatmoDict = {}

            for netatmo in indigo.devices.iter(prId):
                self.debugLog("Got '%s'" % netatmo.name)
                if netatmo.enabled:
                    netatmoDevice = indigo.devices[netatmo.id]
                    # self.errorLog('Found:%s' % netatmoDevice)
                    if netatmoDevice.configured:
                        module = netatmoDevice.pluginProps['moduleName']
                        station = netatmoDevice.pluginProps['stationName']
                        if self.logLevel > 1: self.debugLog("Found Netatmo device '%s' (%s)" % (netatmoDevice .name, module))

                        netatmoDict[station] = netatmoDict.get(station, {})
                        netatmoDict[station][module] = indigo.devices[netatmoDevice]
                    else:
                        self.errorLog("Skipping Indigo device '%s'. Configuration not yet completed." % (netatmoDevice.name))

            for station in netatmoDict:
                if self.logLevel > 1: self.debugLog("Reading Netatmo Station %s" % (station))
                deviceData = lnetatmo.DeviceList(authorization).lastData(station=station)
                if deviceData == 'error':
                    indigo.server.log(u'Server error. Will retry in %s seconds' % (self.netatmoFreq*60),  type=self.pluginDisplayName, isError=True)
                    return
                else:
                    if self.logLevel > 2: self.debugLog("Read device data list: %s" % (deviceData))

                    for module in netatmoDict[station]:
                        if self.logLevel > 1: self.debugLog("Reading Netatmo module %s" % (module))

                        try:
                            for measure in deviceData[module]:
                                if measure == "When":
                                    deviceData[module]["Observation_Time"]= lnetatmo.toTimeString(self, deviceData[module][measure])
                                    del deviceData[module][measure]
                                    measure = "Observation_Time"

                                if measure == "Battery_Level":
                                    deviceData[module]["batteryLevel"]= int(deviceData[module][measure])*100/5640
                                    del deviceData[module][measure]
                                    measure = "batteryLevel"

                                if self.netatmoUnits == "us":
                                    if measure == "Temperature":
                                        deviceData[module][measure] = (deviceData[module][measure] * 9/5) + 32
                                    if measure == "Pressure":
                                        deviceData[module][measure] = deviceData[module][measure] / 33.86389

                                if (measure != ""):
                                    netatmoDict[station][module].updateStateOnServer(key=measure, value=deviceData[module][measure], decimalPlaces=2)
                        except Exception, e:
                            self.errorLog("Error: -%s- reading data for Indigo device '%s'" % (e, netatmoDict[station][module].name))

   ########################################
    def writeNetatmo(self, prDevice, theFunction, theVal):
        if self.logLevel > 1: indigo.server.log(u'Entered: Funct wrteNetatmo' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        return

    ########################################
    def runConcurrentThread(self):
        if self.logLevel > 1: indigo.server.log(u'Entered: Funct runConcurrantThread' ,  type=self.pluginDisplayName + ' Debug', isError=False)

        try:
            while self.runNetatmo:
                self.readNetatmo()
                self.sleep(self.netatmoFreq*60)
        except self.StopThread:
            if self.logLevel > 0: indigo.server.log(u'Stopping Netatmo plugin',  type=self.pluginDisplayName, isError=False)
            pass
        except Exception, e:
            indigo.server.log(u'Plugin stopping. Reason = %s' % (e), type=self.pluginDisplayName, isError=True)

            if self.logLevel > 0: indigo.server.log(u'Stopping Netatmo device read loop',  type=self.pluginDisplayName, isError=False)
            pass


    ########################################
    # Netatmo Action callback
    ######################
    def actionControl(self, action, dev):
        if self.logLevel > 1: indigo.server.log(u'Entered: Funct actionControl' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        if self.logLevel > 3: self.debugLog('Requested action: %s' % (action))

        if action.pluginTypeId == 'pollNetatmo':
            self.readNetatmo()

    ########################################
    # UI Validate, Close, and Actions defined in Actions.xml:
    ########################################
    def validateDeviceConfigUi(self, valuesDict, typeId, devId):
        if self.logLevel > 1: indigo.server.log(u'Entered: Funct validateDeviceConfigUi' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        # We really should poll Netatmo to verify the existance of the device and module
        return (True, valuesDict)

   ########################################
    def closedPrefsConfigUi(self, valuesDict, userCancelled):
        if self.logLevel > 1: indigo.server.log(u'Entered: Funct closedPrefsConfigUi' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        if userCancelled is False:
            (self.logLevel, self.debug) = setLogLevel(self, self.pluginDisplayName, valuesDict["showDebugInfo1"])
            self.userId = valuesDict["userId"]
            self.userPass = valuesDict["userPass"]
            self.netatmoUnits = valuesDict["netatmoUnits"]
            self.netatmoFreq = int(valuesDict["netatmoFreq"])
            self.netatmoTimeout = int(valuesDict["netatmoTimeout"])

            socket.setdefaulttimeout(self.netatmoTimeout)

            if self.logLevel > 0: indigo.server.log("Plugin configuration re-loaded. Polling Netatmo's web server every %s minutes with a %s second timeout"
                                                    % (self.netatmoFreq, self.netatmoTimeout), type=self.pluginDisplayName)

            self.readNetatmo()

    ########################################
    def closedDeviceConfigUi(self, valuesDict, userCancelled, typeId, devId):
        if self.logLevel > 1: indigo.server.log(u'Entered: Funct closedDeviceConfigUi' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        if userCancelled is False:
            if self.logLevel > 0: indigo.server.log("Netatmo device configuration changed. Polling Netatmo's web server for an update")

            self.readNetatmo()
