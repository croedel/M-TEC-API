#!/usr/bin/env python3
"""
This project enables to read data from M-TEC energybutler cloud service.
It bases on re-engineering of M-TEC's Web monitoring portal.
https://energybutler.mtec-portal.com
(c) 2023 by Christian Rödel 
"""
from config import cfg
import logging
import requests
import hashlib
import base64
import json
import time
from datetime import datetime
from http.client import HTTPConnection

#-------------------------------------------------
class MTECapi:
    headers = None
    topology = {}
    retry = 0

    #-------------------------------------------------
    def __init__( self ):
        self.email = cfg["PV_EMAIL"]
        self.password = cfg["PV_PASSWORD"]
        # Login
        self._login()
        # Query (and cache) topology info
        self.query_base_info()
        for station_id in self.topology: # loop over all stations
            self.query_device_list( station_id )

    #-------------------------------------------------
    def _getTimezoneOffset( self ):
        ts = time.time()
        utc_offset_sec = (datetime.fromtimestamp(ts) - datetime.utcfromtimestamp(ts)).total_seconds()
        return int(utc_offset_sec / 60) # minutes
    
    #-------------------------------------------------
    def _login( self ):    
        self._set_headers( "" ) # clear evtl. existing token data
        if( self.email == "" ):
            logging.info( "Executing login with demo account" )
            r_login = self._api_demo_login()  
        else:   
            r_login = self._api_login( )
        
        if r_login["code"] == "1000000":
            self._set_headers( r_login["data"]["token"] )
            return True
        else:
            logging.error( "Login error: {:s}".format( str(r_login)) )
            return False

    #-------------------------------------------------
    def _api_demo_login( self ):
        url = "login/demoManager"
        email = cfg["PV_DEMO_ACCOUNT"]
        payload = { 
            "channel": 1, 
            "email": email
        }
        json_data = self._do_API_call( url, payload=payload, method="POST" )
        return json_data
    
    #-------------------------------------------------
    def _api_login( self ):
        url = "login/manager"
        salt = hashlib.md5( self.password.encode() ).hexdigest()
        password_b64 = base64.b64encode( salt.encode() ).decode()
        payload = { 
            "channel": 1, 
            "email": self.email, 
            "password": password_b64, 
            "salt": salt 
        }
        json_data = self._do_API_call( url, payload=payload, method="POST" )
        return json_data

    #-------------------------------------------------
    def _set_headers( self, token ):
        self.headers = { 
            "Accept": "application/json, text/javascript, */*; q=0.01", 
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US",
            "Authorization": token,
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json; charset=UTF-8",
            "DNT": "1",
            "Host": "energybutler.mtec-portal.com",
            "Pragma": "no-cache",
        }

    #---------------------------------------------
    def _do_API_call( self, url, params=None, payload=None, method="GET" ):
        result = {}
        try:
            response = requests.request( method, cfg["PV_BASE_URL"]+url, headers=self.headers, params=params, 
                                        json=payload, timeout=cfg["PV_TIMEOUT"] )
        except requests.exceptions.RequestException as err:
            logging.error( "Couldn't request REST API: {:s} {:s} ({:s}) Exception {:s}".format(url, method, str(payload), str(err)) )
            result["code"] = "-1"
        else:
            if response.status_code == 200:
                result = response.json()
                if result["code"] == "3010022":     # Login timeout - retry
                    if self.retry < cfg["PV_MAX_LOGIN_RETRY"]:
                        self.retry += 1
                        logging.info( "Token expired - try re-login ({:n}/{:n})".format( self.retry, cfg["PV_MAX_LOGIN_RETRY"]) )
                        if self._login():
                            result = self._do_API_call( url, params, payload, method )
                            if result["code"] == "1000000":
                                self.retry = 0                 
                    else:    
                        logging.error( "Re-login failed. Giving up." )
            else:
                logging.error( "Couldn't request REST API: {:s} {:s} ({:s}) Response {}".format(url, method, str(payload), response) )
        return result    

    #-------------------------------------------------
    def query_base_info( self ):
        url = "basePowerStationInfo/getRunningOverview"
        params = {
            "income": 0.32        # TODO: find out what that means
        }
        json_data = self._do_API_call( url, params=params, method="GET" )
        if json_data["code"] == "1000000":
            if not self.topology:
                # cache stations
                for list in json_data["data"]["top10List"]:
                    self.topology[list["stationId"]] = { 
                        "name": list["stationName"],
                        "devices": {} 
                    }
            return json_data["data"]
        else:
            logging.error( "Error while retrieving base info: {}".format( str(json_data) ) )

    #-------------------------------------------------
    def query_device_list( self, stationId ):
        url = "managerv2/station/devices/query"
        params = {
            "stationId": stationId      
        }
        json_data = self._do_API_call( url, params=params, method="GET"  )
        if json_data["code"] == "1000000":
            # cache devices
            for list in json_data["data"]:
                self.topology[stationId]["devices"][list["deviceId"]] = {
                    "name": list["deviceName"],
                    "deviceSn": list["deviceSn"],
                    "deviceType": list["deviceType"],
                    "modelType": list["modelType"]
                }    
            return True
        else:
            logging.error( "Error while retrieving device list for stationId '{}': {}".format( stationId, str(json_data) ) )
            return False

    #-------------------------------------------------
    def lookup_direction( self, direction ):
        if direction == 1:
            return "obtain"
        elif direction == 2:
            return "feed in" 
        elif direction == 3:
            return "idle"       

    #-------------------------------------------------
    def query_station_data( self, stationId ):            
        url = "curve/station/getSingleStationDataV2"
        params = {
            "id": stationId      
        }
        json_data = self._do_API_call( url, params=params, method="GET" )
        if json_data["code"] == "1000000":
            # map data into data structure
            d = json_data["data"]
            data = {}
            data["stationId"] = stationId
            data["stationName"] = self.topology[str(stationId)]["name"]
            data["stationRunStatus"] = d["stationRunStatus"]
            data["stationRunType"] = d["stationRunType"]
            data["lackMaster"] = d["lackMaster"]

            data["todayEnergy"] =  { 
                "value": d["accumulatedData"]["todayEnergy"],  
                "unit": d["accumulatedData"]["todayEnergyUnit"]  
            }
            data["monthEnergy"] = { 
                "value": d["accumulatedData"]["monthEneregy"], 
                "unit": d["accumulatedData"]["monthEneregyUnit"] 
            }
            data["yearEnergy"] =   { 
                "value": d["accumulatedData"]["yearEnergy"],   
                "unit": d["accumulatedData"]["yearEnergyUnit"]  
            }
            data["totalEnergy"] =  { 
                "value": d["accumulatedData"]["totalEnergy"],  
                "unit": d["accumulatedData"]["totalEnergyUnit"]  
            }

            data["PV"] = { 
                "value": d["dataNodeMap"]["inputNode"]["currentData"],
                "unit": d["dataNodeMap"]["inputNode"]["currentDataUnit"], 
                "direction": d["dataNodeMap"]["inputNode"]["flowDirection"]
            }         
            data["load"] = {
                "value": d["dataNodeMap"]["loadNode"]["currentData"], 
                "unit": d["dataNodeMap"]["loadNode"]["currentDataUnit"], 
                "direction": d["dataNodeMap"]["loadNode"]["flowDirection"] 
            }
            data["battery"] = {
                "value": d["dataNodeMap"]["batteryNode"]["currentData"], 
                "unit": d["dataNodeMap"]["batteryNode"]["currentDataUnit"], 
                "direction": d["dataNodeMap"]["batteryNode"]["flowDirection"], 
                "SOC": d["dataNodeMap"]["batteryNode"]["otherData"] 
            }
            data["grid"] = {
                "value": d["dataNodeMap"]["meterNode"]["currentData"], 
                "unit": d["dataNodeMap"]["meterNode"]["currentDataUnit"], 
                "direction": d["dataNodeMap"]["meterNode"]["flowDirection"] 
            }
            return data
        else:
            logging.error( "Error while retrieving device list for stationId '{}': {}".format( stationId, str(json_data) ) )
            
    #-------------------------------------------------
    def query_usage_data( self, stationId, durationType, dateTime=None ): 
        if durationType=="day" or durationType=="daysummary": 
            return self._query_usage_data_day( stationId, durationType, dateTime )
        else:
            return self._query_usage_data( stationId, durationType, dateTime )

    #-------------------------------------------------
    def _query_usage_data_day( self, stationId, durationType, dateTime=None ): 
        url = "curve/station/queryStationCurve"
        date_str = ""
        if dateTime == None:
            dateTime = datetime.now()

        dt = 1
        date_str = dateTime.strftime("%Y-%m-%d")
        payload = {
            "stationId": stationId,
            "durationType": dt,
            "date": date_str,
            "stationType": 0,
            "timeZoneOffset": self._getTimezoneOffset(),
            "type": "powerflow"
        }
        json_data = self._do_API_call( url, payload=payload, method="POST" )
        if json_data["code"] == "1000000":
            if durationType=="day":
                return self._parse_usage_data_day( json_data )
            elif durationType=="daysummary":
                return self._parse_usage_data_day_summary( json_data )
        else:
            logging.error( "Error while retrieving usage data for stationId '{}': {}".format( stationId, str(json_data) ) )
            return False

    #-------------------------------------------------
    def _query_usage_data( self, stationId, durationType, dateTime=None ): 
        url = "curve/station/queryStationBarChart"
        date_str = ""
        if dateTime == None:
            dateTime = datetime.now()

        if durationType=="month":
            dt = 2
            date_str = dateTime.strftime("%Y-%m")
        elif durationType=="year":
            dt = 3
            date_str = dateTime.strftime("%Y")
        elif durationType=="lifetime":
            dt = 4
                        
        payload = {
            "stationId": stationId,
            "durationType": dt,
            "date": date_str,
            "stationType": 0,
            "timeZoneOffset": self._getTimezoneOffset(),
            "type": "update"
        }
        json_data = self._do_API_call( url, payload=payload, method="POST" )
        if json_data["code"] == "1000000":
            return self._parse_usage_data( date_str, json_data )
        else:
            logging.error( "Error while retrieving usage data for stationId '{}': {}".format( stationId, str(json_data) ) )
            return False

    #-------------------------------------------------
    def _parse_usage_data_day_summary( self, json_data ):            
        # map data into data structure (daily summary)
        data = {}
        d = json_data["data"]["eRatioGraph"]
        data["day_grid_load"] = d.get("eMeterTotalBuy") 
        data["day_grid_feed"] = d.get("eMeterTotalSell")
        data["day_usage"] = d.get("eUse")
        data["day_usage_self"] = d.get("eUseSelf") 
        data["day_total"] = d.get("eDayTotal")
        return data

    #-------------------------------------------------
    def _parse_usage_data_day( self, json_data ):            
        # map data into data structure (daily is different from the other time ranges)
        data = []
        d = json_data["data"]["curve"]
        for i in d:
            ts = i.get("dateStamp") 
            load = i.get("loadPower") 
            grid = i.get("pMeter") 
            PV = i.get("power") 
            battery = i.get("battery") 
            SOC = i.get("SOC")
            if ts and load and grid and PV and battery and SOC:
                data.append( { "ts": ts, "load": load, "grid": grid, "PV": PV, "battery": battery, "SOC": SOC } )
        return data

    #-------------------------------------------------
    def _parse_usage_data( self, date_str, json_data ):            
        # map data into data structure
        d = json_data["data"]["curve"]
        data = []
        for i in d:
            if date_str: # month or year
                date = date_str + "-" + i.get("date") 
            else: # lifetime
                date = i.get("date") 
            grid_load = i.get("ebuytotal") 
            grid_feed = i.get("eselltotal") 
            battery_load = i.get("ebatteryDischarge") 
            battery_feed = i.get("ebatteryCharge")
            pv_production = i.get("eTotal")    
            load = i.get("eusetotal") 

            if date and pv_production:
                data.append( { "date": date, "load": load, "pv_production": pv_production,
                    "grid_load": grid_load, "grid_feed": grid_feed, "battery_load": battery_load, "battery_feed": battery_feed } )
        return data

    
    #-------------------------------------------------
    def query_device_data( self, deviceId ):
        url = "device/getDeviceDataV3"
        params = {
            "id": deviceId     
        }
        json_data = self._do_API_call( url, params=params, method="GET" )
        if json_data["code"] == "1000000":
            # map data into data structure
            data = {}     
            for node in json_data["data"]["config"]:
                if node["labelId"] == 201:  
                    
                    data["inverter"] = {}
                    for d in node["data"]:
                        data["inverter"][d["field"]] = d["value"] 

                elif node["labelId"] == 203:   
                    data["battery"] = {}
                    for d in node["data"]:
                            data["battery"][d["field"]] = d["value"] 
                
                elif node["labelId"] == 206:
                    data["grid"] = {}
                    for phase in node["data"]:
                        for _, d in phase.items():
                            if d.get("field"):
                                data["grid"][d["field"]] = d["value"] 
                
                elif node["labelId"] == 502:            
                    data["PV"] = {}
                    for pv in node["data"]:
                        for _, d in pv.items():
                            if d.get("field"):
                                data["PV"][d["field"]] = d["value"] 

            return data
        else:
            logging.error( "Error while retrieving device data for deviceId '{}': {}".format( deviceId, str(json_data) ) )
            return False

    #-------------------------------------------------
    def getStations( self ):
        stations = []
        for station_id, station_data in self.topology.items():
            item = [station_id, station_data]   
            stations.append(item)
        return stations

    #-------------------------------------------------
    def getDevices( self, station_id ):
        devices = []
        try:
            device_list = self.topology[str(station_id)]["devices"]
            for device_id, device_data in device_list.items():
                item = [device_id, device_data]
                devices.append(item)
        except:
            logging.error( "Couldn't get devices for station '{}'".format( station_id ) )
        return devices
    
#-------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig( level=logging.DEBUG, format="%(asctime)s : %(levelname)s : %(message)s" )

# uncomment following lines to debug https calls
#    HTTPConnection.debuglevel = 1
#    requests_log = logging.getLogger("urllib3")
#    requests_log.setLevel(logging.DEBUG)
#    requests_log.propagate = True

