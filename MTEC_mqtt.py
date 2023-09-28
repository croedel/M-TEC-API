#!/usr/bin/env python3
"""
MQTT server for M-TEC Energybutler
"""

from config import cfg
import MTECapi
import logging
import time

try:
  import paho.mqtt.client as mqttcl
  import paho.mqtt.publish as publish
except Exception as e:
  logging.warning("MQTT not set up because of: {}".format(e))

# ============ MQTT ================
def on_mqtt_connect(mqttclient, userdata, flags, rc):
  logging.info("Connected to MQTT broker")

def on_mqtt_message(mqttclient, userdata, message):
  try:
    msg = message.payload.decode("utf-8")
    topic = message.topic.split("/")
  except Exception as e:
    logging.warning("Error while handling MQTT message: {}".format(str(e)))

def mqtt_start(): 
  try: 
    client = mqttcl.Client()
    client.username_pw_set(cfg['MQTT_LOGIN'], cfg['MQTT_PASSWORD']) 
    client.connect(cfg['MQTT_SERVER'], cfg['MQTT_PORT'], keepalive = 60) 
    client.on_connect = on_mqtt_connect
    client.on_message = on_mqtt_message
    client.loop_start()
    logging.info('MQTT server started')
    return client
  except Exception as e:
    logging.warning("Couldn't start MQTT: {}".format(str(e)))

def mqtt_stop(client):
  try: 
    client.loop_stop()
    logging.info('MQTT server stopped')
  except Exception as e:
    logging.warning("Couldn't stop MQTT: {}".format(str(e)))

def mqtt_publish( topic, payload ):  
  auth = {
    'username': cfg['MQTT_LOGIN'],
    'password': cfg['MQTT_PASSWORD'] 
  }  
  logging.debug("Publish MQTT command {}: {}".format(topic, payload))
  try:
    publish.single(topic, payload=payload, hostname=cfg['MQTT_SERVER'], port=cfg['MQTT_PORT'], auth=auth)
  except Exception as e:
    logging.error("Could't send MQTT command: {}".format(str(e)))

# =============================================

def normalize( data ):
  if( isinstance(data, dict) and "value" in data and "unit" in data ):
    # Normalize power to W
    if data["unit"] == "kW":
      data["value"] *= 1000
      data["unit"] = "W" 
    elif data["unit"] == "MW":
      data["value"] *= 1000000
      data["unit"] = "W" 
    elif data["unit"] == "GW":
      data["value"] *= 1000000000          
      data["unit"] = "W" 
    # Normalize work to kWh
    elif data["unit"] == "Wh":
      data["value"] /= 1000
      data["unit"] = "kWh" 
    elif data["unit"] == "MWh":
      data["value"] *= 1000
      data["unit"] = "kWh" 
    elif data["unit"] == "GWh":
      data["value"] *= 1000000          
      data["unit"] = "kWh" 
  return data            

# read station data from MTEC device
def read_MTEC_station_data( api, station_id ):
  data = api.query_station_data(station_id)
  pvdata = {}
  pvdata["day_production"] = normalize(data["todayEnergy"])              # Energy produced by the PV today
  pvdata["month_production"] = normalize(data["monthEnergy"])            # Energy produced by the PV this month
  pvdata["year_production"] = normalize(data["yearEnergy"])              # Energy produced by the PV this year
  pvdata["total_production"] = normalize(data["totalEnergy"])            # Energy produced by the PV in total
  pvdata["current_PV"] = normalize(data["PV"])                           # Current flow from PV
  pvdata["current_grid"] = normalize(data["grid"])                       # Current flow from/to grid
  pvdata["current_battery"] = normalize(data["battery"])                 # Current flow from/to battery
  pvdata["current_battery_SOC"] = { "value": data["battery"]["SOC"], "unit": "%" }   # Current battery SOC
  pvdata["current_load"] = normalize(data["load"])                       # Current consumed energy
  pvdata["grid_interrupt"] = { "value": data["lackMaster"], "unit": "" }  # Grid interrup flag

  # grid and battery: Invert to negativ value if direction == 2 ("feed in")
  if data["grid"]["direction"] == 2:
    pvdata["current_grid"] *= -1  
  if data["battery"]["direction"] == 2:
    pvdata["current_battery"] *= -1  

  return pvdata

# read device data from MTEC device
def read_MTEC_device_data( api, device_id ):
  data = api.query_device_data(device_id)
  pvdata = {}
  pvdata["battery_P"] = normalize(data["battery"]["Battery_P"])
  pvdata["battery_V"] = data["battery"]["Battery_V"]
  pvdata["battery_I"] = data["battery"]["Battery_I"]
  pvdata["battery_SOC"] = data["battery"]["SOC"]
  pvdata["inverter_A_P"] = normalize(data["grid"]["Invt_A_P"])
  pvdata["inverter_A_V"] = data["grid"]["Vgrid_PhaseA"]
  pvdata["inverter_A_I"] = data["grid"]["Igrid_PhaseA"]
  pvdata["inverter_B_P"] = normalize(data["grid"]["Invt_B_P"])
  pvdata["inverter_B_V"] = data["grid"]["Vgrid_PhaseB"]
  pvdata["inverter_B_I"] = data["grid"]["Igrid_PhaseB"]
  pvdata["inverter_C_P"] = normalize(data["grid"]["Invt_C_P"])
  pvdata["inverter_C_V"] = data["grid"]["Vgrid_PhaseC"]
  pvdata["inverter_C_I"] = data["grid"]["Igrid_PhaseC"]
  pvdata["grid_A_P"] = normalize(data["grid"]["PmeterPhaseA"])
  pvdata["grid_B_P"] = normalize(data["grid"]["PmeterPhaseB"])
  pvdata["grid_C_P"] = normalize(data["grid"]["PmeterPhaseC"])

  for string in data["PV"]:
    pvdata["PV_"+string["name"]["value"]+"_P"] = normalize(string["power"]["value"])
    pvdata["PV_"+string["name"]["value"]+"_V"] = string["voltage"]["value"]
    pvdata["PV_"+string["name"]["value"]+"_I"] = string["current"]["value"]

  return pvdata

# write data to MQTT
def write_to_MQTT( pvdata, base_topic ):
  for param, data in pvdata.items():
    topic = base_topic + param
    if isinstance(data, dict):
      if isinstance(data["value"], float):  
        payload = cfg['MQTT_FLOAT_FORMAT'].format( data["value"] )
      elif isinstance(data["value"], bool):  
        payload = "{:d}".format( data["value"] )
      else:
        payload = data["value"]
    else:   
      if isinstance(data, float):  
        payload = cfg['MQTT_FLOAT_FORMAT'].format( data )
      elif isinstance(data, bool):  
        payload = "{:d}".format( data )
      else:
        payload = data  
    logging.debug("- {}: {}".format(topic, str(payload)))
#    mqtt_publish( topic, payload )

#==========================================
def main():
  logging.basicConfig()
  if cfg['DEBUG'] == True:
    logging.getLogger().setLevel(logging.DEBUG)
  logging.info("Starting")

  # Inititialization
  mqttclient = mqtt_start()
  api = MTECapi.MTECapi()
  stations = api.getStations()

  while True:
    for station_id, station_data in stations:
      devices = api.getDevices(station_id)
      pvdata = read_MTEC_station_data(api, station_id)
      if cfg['WRITE_STATION_DATA'] == True:
        logging.debug("Station {} ({})".format( station_data['name'], station_id ))
        base_topic = cfg['MQTT_TOPIC'] + '/' + station_data['name'] + '/'
        write_to_MQTT( pvdata, base_topic )
      for device_id, device_data in devices: 
        pvdata = read_MTEC_device_data(api, device_id)
        if cfg['WRITE_DEVICE_DATA'] == True:
          logging.debug("Device {} ({})".format( device_data['name'], device_id ))
          base_topic = cfg['MQTT_TOPIC'] + '/' + station_data['name'] + '/' + device_data['name'] + '/'
          write_to_MQTT( pvdata, base_topic )

    logging.debug("Sleep {}s".format( cfg['POLL_FREQUENCY'] ))
    time.sleep(cfg['POLL_FREQUENCY'])

  mqtt_stop(mqttclient)
  logging.info("Stopped")

if __name__ == '__main__':
  main()
