#!/usr/bin/env python3
"""
This tool enables to query MTECapi and can act as demo on how to use the API
(c) 2023 by Christian Rödel 
"""
from config import cfg
import logging
import json
import MTECapi

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

  # Query data
  data = api.query_station_data( stations[i][0] )
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

  # Display list of available devices
  devices = api.getDevices(stations[i][0])
  idx=0
  for device_id, device_data in devices:
    print( "  (#{}) DeviceId '{}' : {}".format( idx, device_id, device_data['name']) ) 
    idx+=1
  i = int(input("Please select device #: "))

  if i > idx-1:
    print("Invalid #")
    return

  # Query data
  data = api.query_device_data( devices[i][0] )
  if data: 
    print( "--------------------------------------------------------" )
    print( json.dumps(data, indent=2) )


#-------------------------------
def main():
  api = MTECapi.MTECapi()

  while True:
    print( "-------------------------------------" )
    print( "Menu:")
    print( "  1: List system topology" )
    print( "  2: List station data" )
    print( "  3: List device data" )
    print( "  x: Exit" )
    opt = input("Please select: ")
    if opt == "1": 
      show_topology(api)
    elif opt == "2":  
      show_station_data(api)
    elif opt == "3":  
      show_device_data(api)
    elif opt == "x" or opt == "X":  
      break
  
  print( "Bye!")

#-------------------------------
if __name__ == '__main__':
  main()
