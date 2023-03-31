#!/usr/bin/env python3
"""
This tool enables to query MTECapi and can act as demo on how to use the API
(c) 2023 by Christian Rödel 
"""
from config import cfg
import json
import datetime
from dateutil.relativedelta import relativedelta
import MTECapi

#-----------------------------
def let_user_select_station( api ):
  # Display list of available stations
  stations = api.getStations()
  idx=0
  for station_id, station_data in stations:
    print( "  (#{}) StationId '{}' : {}".format( idx, station_id, station_data['name']) )
    idx+=1 
  i = int(input("Please select station #: "))

  if i > idx-1:
    print("Invalid #")
    return 
  else:
    return stations[i][0]

#-----------------------------
def let_user_select_device( api, stationId ):
  # Display list of available devices
  devices = api.getDevices(stationId)
  idx=0
  for device_id, device_data in devices:
    print( "  (#{}) DeviceId '{}' : {}".format( idx, device_id, device_data['name']) ) 
    idx+=1
  i = int(input("Please select device #: "))

  if i > idx-1:
    print("Invalid #")
    return
  else:
    return devices[i][0]

#-----------------------------
def show_topology( api ):
  stations = api.getStations()

  # Display list of available stations
  print( "--------------------------------------------------------" )
  for station_id, station_data in stations:
    print( "StationId '{}' : {}".format( station_id, station_data['name']) )
    devices = api.getDevices( station_id )
    for device_id, device_data in devices:
      print( "- DeviceId '{}' : {}".format( device_id, device_data['name']) )
      print( "  Model:    {}".format( device_data['modelType']) )
      print( "  SerialNo: {}".format( device_data['deviceSn']) )

#-----------------------------
def show_station_data ( api ):
  stationId = let_user_select_station(api)
  data = api.query_station_data( stationId )
  idx=1
  if data: 
    print( "--------------------------------------------------------" )
    print( "Current data: for station '{}': {}".format( data["stationId"], data["stationName"] ) )
    print( "- Run status:     {}".format( data["stationRunStatus"] ))   # TODO: find out meaning (1=OK)?
    print( "- Run type:       {}".format( data["stationRunType"] ))       # TODO: find out meaning  
    print( "- Lack of master: {}".format( data["lackMaster"] ))     # TODO: find out meaning (grid not available?)  
    print( "PV Energy:" )
    print( "- Today:   {} {}".format( data["todayEnergy"]["value"], data["todayEnergy"]["unit"] ))
    print( "- Month:   {} {}".format( data["monthEnergy"]["value"], data["monthEnergy"]["unit"] ))
    print( "- Year:    {} {}".format( data["yearEnergy"]["value"], data["yearEnergy"]["unit"] ))
    print( "- Total:   {} {}".format( data["totalEnergy"]["value"], data["totalEnergy"]["unit"] ))
    print( "Current stats:" )
    print( "- PV:      {} {}, direction: {} ({})".format( data["PV"]["value"], data["PV"]["unit"], 
          data["PV"]["direction"], api.lookup_direction(data["PV"]["direction"] )))
    print( "- grid:    {} {}, direction: {} ({})".format( data["grid"]["value"], data["grid"]["unit"], 
          data["grid"]["direction"], api.lookup_direction(data["grid"]["direction"])))
    print( "- battery: {} {} , direction: {} ({}), SOC: {}%".format( data["battery"]["value"], data["battery"]["unit"], 
          data["battery"]["direction"], api.lookup_direction(data["battery"]["direction"]), 
          data["battery"]["SOC"]))
    print( "- load:    {} {}, direction: {} ({})".format( data["load"]["value"], data["load"]["unit"], 
          data["load"]["direction"], api.lookup_direction(data["load"]["direction"])))

#-----------------------------
def show_device_data( api ):
  stationId = let_user_select_station( api )
  deviceId = let_user_select_device( api, stationId )
  data = api.query_device_data( deviceId )
  if data: 
    print( "--------------------------------------------------------" )
    print( json.dumps(data, indent=2) )

#-----------------------------
def show_usage_data_day( api ):
  stationId = let_user_select_station( api )
  days = int(input("Select no. of days you want to export: "))

  end_date = datetime.datetime.now()
  date = end_date - datetime.timedelta(days=days)
  print( "--------------------------------------------------------" )
  print( "timestamp, load, grid, PV, battery, SOC")

  while date <= end_date:
    data = api.query_usage_data( stationId, "day", date )
    if data: 
      for item in data:
        print( "{}, {}, {}, {}, {}, {}".format( item["ts"], item["load"], item["grid"], 
                                             item["PV"], item["battery"], item["SOC"] ) )
    date += datetime.timedelta(days=1)

#-----------------------------
def show_usage_data_month( api ):
  stationId = let_user_select_station( api )
  months = int(input("Select no. of months you want to export: "))

  today = datetime.datetime.now()
  end_date = datetime.datetime( today.year, today.month, 1 )
  date = end_date - datetime.timedelta(days=(months-1)*30)
  print( "--------------------------------------------------------" )
  print( "date, load, pv_production, grid_load, grid_feed, battery_load, battery_feed")

  while date <= end_date:
    data = api.query_usage_data( stationId, "month", date )
    if data: 
      for item in data:
        print( "{}, {}, {}, {}, {}, {}, {}".format( item["date"], item["load"], item["pv_production"],
                                              item["grid_load"], item["grid_feed"], 
                                              item["battery_load"], item["battery_feed"] ) )
    date += relativedelta(months=1)

#-------------------------------
def main():
  api = MTECapi.MTECapi()

  while True:
    print( "-------------------------------------" )
    print( "Menu:")
    print( "  1: List system topology" )
    print( "  2: List station data" )
    print( "  3: List device data" )
    print( "  4: Usage data (day)" )
    print( "  5: Usage data (month)" )
    print( "  x: Exit" )
    opt = input("Please select: ")
    if opt == "1": 
      show_topology(api)
    elif opt == "2":  
      show_station_data(api)
    elif opt == "3":  
      show_device_data(api)
    elif opt == "4":
      show_usage_data_day(api)  
    elif opt == "5":
      show_usage_data_month(api)  
    elif opt == "x" or opt == "X":  
      break
  
  print( "Bye!")

#-------------------------------
if __name__ == '__main__':
  main()
