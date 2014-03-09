# Published Jan 2013
# Author: philippelt@users.sourceforge.net
# Modifications: indigo@perlman.com
# Public domain source code

# This code provides access to the Netatmo (Internet weather station) devices
# for the Indigo Home Automation software (www.perceptivesystems.com)

# PythonAPI Netatmo REST data access
# coding=utf-8

import simplejson as json
import time
from urllib import urlencode
import urllib2
import socket
import __builtin__
import indigo

# Common definitions

_BASE_URL = "http://api.netatmo.net/"
_AUTH_REQ = _BASE_URL + "oauth2/token"
_GETUSER_REQ = _BASE_URL + "api/getuser"
_DEVICELIST_REQ = _BASE_URL + "api/devicelist"
_GETMEASURE_REQ = _BASE_URL + "api/getmeasure"

# User-based specs

_CLIENT_ID = "5188fe1d19775918c2000012"                         # From Netatmo app registration
_CLIENT_SECRET = "6yej5k7DFlK3yFh6kotA3Rptua"
_USERNAME = "foo"
_PASSWORD = "foo"


class ClientAuth:
    "Request authentication and keep access token available through token method. Renew it automatically if necessary"

    def __init__(self, username, password, clientId=_CLIENT_ID, clientSecret=_CLIENT_SECRET):
        self.pluginDisplayName = __builtin__.pluginDisplayName 
        self.logLevel = __builtin__.logLevel
        if self.logLevel > 1: indigo.server.log(u'Entered: ClientAuth init' ,  type=self.pluginDisplayName + ' Debug', isError=False)

        postParams = {
            "grant_type": "password",
            "client_id": clientId,
            "client_secret": clientSecret,
            "username": username,
            "password": password
        }
        resp = postRequest(self, _AUTH_REQ, postParams)

        if resp == 'error':
            indigo.server.log(u'Netatmo server error encountered in ClientAuth init',  type=self.pluginDisplayName, isError=True)
            self.expiration = 'error'
        else:
            self._clientId = clientId
            self._clientSecret = clientSecret
            self._accessToken = resp['access_token']
            self.refreshToken = resp['refresh_token']
            self._scope = resp['scope']
            self.expiration = int(resp['expire_in'] + time.time())

    @property
    def accessToken(self):
        "Provide the current or renewed access token"
        if self.logLevel > 1: indigo.server.log(u'Entered: ClientAuth accessToken' ,  type=self.pluginDisplayName + ' Debug', isError=False)

        if self.expiration == 'error':
                indigo.server.log(u'Netatmo server error encountered in ClientAuth accessToken entry',  type=self.pluginDisplayName, isError=True)
                return 'error'

        if self.expiration < time.time():  # Token should be renewed

            postParams = {
                "grant_type": "refresh_token",
                "refresh_token": self.refreshToken,
                "client_id": self._clientId,
                "client_secret": self._clientSecret
            }
            resp = postRequest(self, _AUTH_REQ, postParams)

            if resp == 'error':
                indigo.server.log(u'Netatmo server error encountered in ClientAuth accessToken postRequest',  type=self.pluginDisplayName, isError=True)
                return 'error'
            else:
                self._accessToken = resp['access_token']
                self.refreshToken = resp['refresh_token']
                self.expiration = int(resp['expire_in'] + time.time())

        return self._accessToken


class User:
    "Access to user account information"

    def __init__(self, authData):
        self.pluginDisplayName = __builtin__.pluginDisplayName 
        self.logLevel = __builtin__.logLevel
        if self.logLevel > 1: indigo.server.log(u'Entered: User init' ,  type=self.pluginDisplayName + ' Debug', isError=False)


        postParams = {
            "access_token": authData.accessToken
        }
        resp = postRequest(self, _GETUSER_REQ, postParams)
        if resp == 'error':
            indigo.server.log(u'Netatmo server error encountered in User init',  type=self.pluginDisplayName, isError=True)
            return 'error'
        else:
            self.rawData = resp['body']
            self.id = self.rawData['_id']
            self.devList = self.rawData['devices']
            self.ownerMail = self.rawData['mail']


class DeviceList:
    "Set of stations and modules attached to the user account"

    def __init__(self, authData):
        self.pluginDisplayName = __builtin__.pluginDisplayName 
        self.logLevel = __builtin__.logLevel
        if self.logLevel > 1: indigo.server.log(u'Entered: DeviceList init' ,  type=self.pluginDisplayName + ' Debug', isError=False)

        self.getAuthToken = authData.accessToken
        postParams = {
            "access_token": self.getAuthToken
        }
        resp = postRequest(self, _DEVICELIST_REQ, postParams)
        # indigo.server.log(u'DeviceList init  received %s' % resp,  type=self.pluginDisplayName, isError=True)
        if resp == 'error':
            indigo.server.log(u'Netatmo server error encountered in DeviceList init',  type=self.pluginDisplayName, isError=True)
            return 'error'
        else:
            self.rawData = resp['body']
            self.stations = {}
            for d in self.rawData['devices']: self.stations[d['_id']] = d
            self.modules = {}
            for m in self.rawData['modules']: self.modules[m['_id']] = m
            self.default_station = list(self.stations.values())[0]['station_name']

    def stationByName(self, station=None):
        if self.logLevel > 1: indigo.server.log(u'Entered: DeviceList stationByName' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        if not station: station = self.default_station
        for i, s in self.stations.items():
            if s['station_name'] == station: return self.stations[i]
        return None

    def stationById(self, sid):
        if self.logLevel > 1: indigo.server.log(u'Entered: DeviceList stationById' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        return None if sid not in self.stations else self.stations[sid]

    def moduleByName(self, module, station=None):
        if self.logLevel > 1: indigo.server.log(u'Entered: DeviceList moduleByName' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        s = None
        if station:
            s = self.stationByName(station)
            if not s: return None
        for m in self.modules:
            mod = self.modules[m]
            if mod['module_name'] == module:
                if not s or mod['main_device'] == s['_id']: return mod
        return None

    def moduleById(self, mid, sid=None):
        if self.logLevel > 1: indigo.server.log(u'Entered: DeviceList moduleById' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        s = self.stationById(sid) if sid else None
        if mid in self.modules:
            return self.modules[mid] if not s or self.modules[mid]['main_device'] == s['_id'] else None

    def lastData(self, station=None):
        if self.logLevel > 1: indigo.server.log(u'Entered: DeviceList lastData',  type=self.pluginDisplayName + ' Debug', isError=False)

        if not station:
            station = self.default_station
        s = self.stationByName(station)
        lastD = {}
        if s:
            # indigo.server.log("Got s=%s" % s)
            ds = s['last_data_store'][s['_id']]
            # indigo.server.log("MAIN ==>%s" % ds)
            # lastD[s['module_name']] = {"Temperature": ds['a'], "Pressure": ds['e'], "Noise": ds['S'], "Co2": ds['h'], "Humidity": ds['b'], "When": ds['K']}
            # indigo.server.log("==>%s" % lastD)
            lastD[s['module_name']] = {"Temperature": ds['a'], "Pressure": ds['e'], "Noise": ds['S'], "Co2": ds['h'], "Humidity": ds['b'], "When": ds['K'], "WiFi_Signal": s['wifi_status']}
            for m in s['modules']:
                ds = s['last_data_store'][m]
                # lastD[self.modules[m]['module_name']] = {"Temperature": ds['a'], "Humidity": ds['b'], "When": ds['K']}
                # indigo.server.log("<%s>==>%s" % (m, ds))
                if 'h' in ds:
                    # indigo.server.log("Got Here 1")
                    lastD[self.modules[m]['module_name']] = {"Temperature": ds['a'], "Humidity": ds['b'], "Co2": ds['h'], "When": ds['K'], "RF_Signal": self.modules[m]['rf_status'], "Battery_Level": self.modules[m]['battery_vp']}
                else:
                    # indigo.server.log("Got Here 2")
                    lastD[self.modules[m]['module_name']] = {"Temperature": ds['a'], "Humidity": ds['b'], "When": ds['K'], "RF_Signal": self.modules[m]['rf_status'], "Battery_Level": self.modules[m]['battery_vp']}

            return lastD if len(lastD) else None

    def checkNotUpdated(self, station=None, delay=3600):
        if self.logLevel > 1: indigo.server.log(u'Entered: DeviceList checkNotUpdated' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        res = self.lastData(station)
        ret = []
        for mn, v in res.items():
            if time.time()-v['When'] > delay: ret.append(mn)
        return ret if ret else None

    def checkUpdated(self, station=None, delay=3600):
        if self.logLevel > 1: indigo.server.log(u'Entered: DeviceList checkUpdated' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        res = self.lastData(station)
        ret = []
        for mn, v in res.items():
            if time.time()-v['When'] < delay: ret.append(mn)
        return ret if ret else None

    def getMeasure(self, device_id, scale, mtype, module_id=None, date_begin=None, date_end=None, limit=None, optimize=False):
        if self.logLevel > 1: indigo.server.log(u'Entered: DeviceList getMeasure' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        postParams = {"access_token": self.getAuthToken}
        postParams['device_id'] = device_id
        if module_id: postParams['module_id'] = module_id
        postParams['scale'] = scale
        postParams['type'] = mtype
        if date_begin: postParams['date_begin'] = date_begin
        if date_end: postParams['date_end'] = date_end
        if limit: postParams['limit'] = limit
        postParams['optimize'] = "true" if optimize else "false"
        resp = postRequest(self, _GETMEASURE_REQ, postParams)
        if resp == 'error':
            indigo.server.log(u'Netatmo server error encountered in DeviceList getMeasure',  type=self.pluginDisplayName, isError=True)
            return 'error'
        else:
            return resp

    def MinMaxTH(self, station=None, module=None, frame="last24"):
        if self.logLevel > 1: indigo.server.log(u'Entered: DeviceList MinMaxTH' ,  type=self.pluginDisplayName + ' Debug', isError=False)
        if not station: station = self.default_station
        s = self.stationByName(station)
        if not s:
            s = self.stationById(station)
            if not s: return None
        if frame == "last24":
            end = time.time()
            start = end - 24*3600  # 24 hours ago
        elif frame == "day":
            start, end = todayStamps(self)
        if module:
            m = self.moduleByName(module, s['station_name'])
            if not m:
                m = self.moduleById(s['_id'], module)
                if not m: return None
            # retrieve module's data
            resp = self.getMeasure(
                device_id=s['_id'],
                module_id=m['_id'],
                scale="max",
                mtype="Temperature,Humidity",
                date_begin=start,
                date_end=end)
        else:  # retrieve station's data
            resp = self.getMeasure(
                device_id=s['_id'],
                scale="max",
                mtype="Temperature,Humidity",
                date_begin=start,
                date_end=end)
        if resp:
            T = [v[0] for v in resp['body'].values()]
            H = [v[1] for v in resp['body'].values()]
            return min(T), max(T), min(H), max(H)
        else:
            return None


# Utilities routines

def postRequest(self, url, params):
    if self.logLevel > 1: indigo.server.log(u'Entered: Funct postRequest' ,  type=self.pluginDisplayName + ' Debug', isError=False)
    socket.setdefaulttimeout(30)
    params = urlencode(params)
    headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
    req = urllib2.Request(url=url, data=params, headers=headers)
    try:
        resp = urllib2.urlopen(req).read()

        if self.logLevel > 3: indigo.server.log(u'Funct postRequest received %s' % resp,  type=self.pluginDisplayName + ' Debug', isError=False)
        return json.loads(resp)
    except Exception, e:
        pluginDisplayName="Netatmo plugin"
        indigo.server.log(u'Problem opening Netatmo web site. Reason = %s' % (e), type=pluginDisplayName + ' Debug', isError=True)
        return "error"


def toTimeString(self, value):
    if self.logLevel > 1: indigo.server.log(u'Entered: Funct toTimeString' ,  type=self.pluginDisplayName + ' Debug', isError=False)
    return time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime(int(value)))


def toEpoch(self, value):
    if self.logLevel > 1: indigo.server.log(u'Entered: Funct toEpoch' ,  type=self.pluginDisplayName + ' Debug', isError=False)
    return int(time.mktime(time.strptime(value, "%Y-%m-%d_%H:%M:%S")))


def todayStamps(self):
    if self.logLevel > 1: indigo.server.log(u'Entered: Funct todayStamps' ,  type=self.pluginDisplayName + ' Debug', isError=False)
    today = time.strftime("%Y-%m-%d")
    today = int(time.mktime(time.strptime(today, "%Y-%m-%d")))
    return today, today+3600*24


# Global shortcut
def getStationMinMaxTH(self, station=None, module=None):
    if self.logLevel > 1: indigo.server.log(u'Entered: Funct getStationMinMaxTH' ,  type=self.pluginDisplayName + ' Debug', isError=False)
    authorization = ClientAuth()
    devList = DeviceList(authorization)
    if not station: station = devList.default_station
    lastD = devList.lastData(station)
    if module:
        mname = module
    else:
        mname = devList.stationByName(station)['module_name']
    if time.time()-lastD[mname]['When'] > 3600: result = ["-", "-"]
    else: result = [lastD[mname]['Temperature'], lastD[mname]['Humidity']]
    result.extend(devList.MinMaxTH(station, module))
    return result
