#!/usr/bin/env python3
"""
Command line tool which enables to query MTECapi and show how to use the API
(c) 2023 by Christian Rödel 
"""
import argparse
from config import cfg
import logging
import json
import MTECapi

#-----------------------------
def show_topology( api, args ):
  topo = api.getTopology()
  print( "--------------------------------------------------------" )
  print( "Topology:" )
  for station_id, station_data in topo.items():
    print( "StationId '{}' : {}".format( station_id, station_data['name']) )
    for device_id, device_data in station_data["devices"].items():
      print( "- DeviceId '{}' : {}".format( device_id, device_data['name']) )
      print( "  Model:    {}".format( device_data['modelType']) )
      print( "  SerialNo: {}".format( device_data['deviceSn']) )

#-----------------------------
def show_station_data ( api, args ):
  data = api.query_station_data( args.id ) 
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
  print( "Current status:" )
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
def parse_options():
  epilog = """commands:
  topology:        List topology (stations and devices)
  station <id>:    Query data for station <id>  
  """
  parser = argparse.ArgumentParser(description='M-TEC API command line tool', epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--id', '-i', default=cfg['DEMO_STATION_ID'], help='stationId')
  parser.add_argument('command', choices=["topology", "station"], nargs='?', default="topology" )
  parser.add_argument('param', nargs='?', help="parameter" )
  return parser.parse_args()

#-------------------------------
def main():
  args = parse_options()
  api = MTECapi.MTECapi()

  if args.command == "topology": 
    show_topology(api, args)
  elif args.command == "station":
    show_station_data(api, args)

#-------------------------------
if __name__ == '__main__':
  main()

