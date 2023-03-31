#!/usr/bin/env python3
"""
This is a command line tool which enables to export data from a MTEC device as CSV. 
(c) 2023 by Christian Rödel 
"""
from config import cfg
import datetime
from dateutil.relativedelta import relativedelta
import argparse
import sys
import MTECapi

#-----------------------------
def process_usage_data_day( api, stationId, date, separator ):
  end_date = datetime.datetime.now()

  print( "timestamp;load;grid;PV;battery;SOC")
  while date <= end_date:
    data = api.query_usage_data( stationId, "day", date )
    if data: 
      for item in data:
        line = "{}; {}; {}; {}; {}; {}".format( item["ts"], item["load"], item["grid"], 
                                             item["PV"], item["battery"], item["SOC"] )
        print( line.replace(".", separator) )
    date += datetime.timedelta(days=1)

#-----------------------------
def process_usage_data( api, stationId, durationType, date, separator ):
  end_date = datetime.datetime.now()

  print( "date;load;pv_production;battery_load;battery_feed;grid_load;grid_feed")
  while date <= end_date:
    data = api.query_usage_data( stationId, durationType, date )
    if data: 
      for item in data:
        line = "{}; {}; {}; {}; {}; {}; {}".format( item["date"], item["load"], item["pv_production"],
                            item["battery_load"], item["battery_feed"], item["grid_load"], item["grid_feed"] )
        print( line.replace(".", separator) )
    date += relativedelta(months=1)

#-----------------------------
def parse_options():
  parser = argparse.ArgumentParser(description='MTEC data export tool. Exports data from a MTEC device as CSV', 
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument( '-t', '--type', choices=["day", "month", "year", "lifetime"], required=True, help='Type of data export' )
  parser.add_argument( '-d', '--date', required=True, help="Start date [YYYY-MM-DD]" )
  parser.add_argument( '-n', '--name', help='Your MTEC station name (only required if you have multiple stations)')
  parser.add_argument( '-s', '--separator', help='Set decimal separator (default is ".")' )
  parser.add_argument( '-f', '--file', help='Write data to <FILE> instead of stdout')
  return parser.parse_args()
 
#-------------------------------
def main():
  args = parse_options()
  api = MTECapi.MTECapi()       # Create MTECapi connection
  stations = api.getStations()   # retrieve available stations

  try:
    date = datetime.datetime.strptime( args.date, "%Y-%m-%d" )
  except:
    print( "ERROR - Invalid date format: '{}'. Expecting [YYYY-MM-DD]".format(args.date) )  
    exit(1)

  # lookup stationId by station name (if given as command line parameter) 
  stationId = None
  if args.name: 
    for id, data in stations:
      if data['name'] == args.name:
        stationId = id
    if not stationId:
      print( "ERROR - Unknown station: '{}'".format(args.name) )
      exit(1)     
  else: # default: use first station
    stationId = stations[0][0] 

  # redirect stdout to file (if defined as command line parameter)
  if args.file:  
    try:
      print( "Retrieving data and exporting to '{}' ...".format(args.file) )
      original_stdout = sys.stdout
      sys.stdout = open(args.file, 'w')
    except:  
      print( "ERROR - Unable to create file '{}'".format(args.file) )

  # decimal separator
  if args.separator:
    separator = args.separator
  else:
    separator = "."  
      
  # do the actual export
  if args.type == "day": 
    process_usage_data_day( api, stationId, date, separator )
  else: 
    process_usage_data( api, stationId, args.type, date, separator )

  # cleanup
  if args.file:
    sys.stdout.close()  
    sys.stdout = original_stdout
    print( "done" )

#-------------------------------
if __name__ == '__main__':
  main()
