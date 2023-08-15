#!/usr/bin/env python3
"""
MQTT server for MTEC
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
    client.connect(cfg['MQTT_SERVER'], cfg['MQTT_PORT'], 60) 
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
  logging.debug("Publish MQTT command {}: {} {}".format(topic, payload, str(auth)))
  try:
    publish.single(topic, payload=payload, hostname=cfg['MQTT_SERVER'], port=cfg['MQTT_PORT'], keepalive=10, auth=auth)
  except Exception as e:
    logging.error("Could't send MQTT command: {}".format(str(e)))

# =============================================
# read station data from MTEC device
def read_MTEC_station_data( api, station_id ):
  data = api.query_station_data(station_id)
  pvdata = {}
  pvdata["day_production"] = data["todayEnergy"]              # Energy produced by the PV today
  pvdata["month_production"] = data["monthEnergy"]            # Energy produced by the PV this month
  pvdata["year_production"] = data["yearEnergy"]              # Energy produced by the PV this year
  pvdata["total_production"] = data["totalEnergy"]            # Energy produced by the PV in total
  pvdata["current_PV"] = data["PV"]                           # Current flow from PV
  pvdata["current_grid"] = data["grid"]                       # Current flow from/to grid
  pvdata["current_battery"] = data["battery"]                 # Current flow from/to battery
  pvdata["current_battery_SOC"] = { "value": data["battery"]["SOC"], "unit": "%" }   # Current battery SOC
  pvdata["current_load"] = data["load"]                       # Current consumed energy
  pvdata["grid_interrupt"] = { "value": data["lackMaster"], "unit": "" }  # Grid interrup flag
  return pvdata

# read device data from MTEC device
def read_MTEC_device_data( api, device_id ):
  data = api.query_device_data(device_id)
  pvdata = {}
  pvdata["battery_P"] = data["battery"]["Battery_P"]
  pvdata["battery_V"] = data["battery"]["Battery_V"]
  pvdata["battery_I"] = data["battery"]["Battery_I"]
  pvdata["battery_SOC"] = data["battery"]["SOC"]
  pvdata["inverter_A_P"] = data["grid"]["Invt_A_P"]
  pvdata["inverter_A_V"] = data["grid"]["Vgrid_PhaseA"]
  pvdata["inverter_A_I"] = data["grid"]["Igrid_PhaseA"]
  pvdata["inverter_B_P"] = data["grid"]["Invt_B_P"]
  pvdata["inverter_B_V"] = data["grid"]["Vgrid_PhaseB"]
  pvdata["inverter_B_I"] = data["grid"]["Igrid_PhaseB"]
  pvdata["inverter_C_P"] = data["grid"]["Invt_C_P"]
  pvdata["inverter_C_V"] = data["grid"]["Vgrid_PhaseC"]
  pvdata["inverter_C_I"] = data["grid"]["Igrid_PhaseC"]
  pvdata["grid_A_P"] = data["grid"]["PmeterPhaseA"]
  pvdata["grid_B_P"] = data["grid"]["PmeterPhaseB"]
  pvdata["grid_C_P"] = data["grid"]["PmeterPhaseC"]

  for string in data["PV"]:
    pvdata["PV_"+string["name"]["value"]+"_P"] = string["power"]["value"]
    pvdata["PV_"+string["name"]["value"]+"_V"] = string["voltage"]["value"]
    pvdata["PV_"+string["name"]["value"]+"_I"] = string["current"]["value"]

  return pvdata

# write data to MQTT
def write_to_MQTT( pvdata, base_topic ):
  for param, data in pvdata.items():
    topic = base_topic + param
    if isinstance(data, float):  
      payload = data
    else:  
      payload = data["value"]
    logging.debug("- {}: {}".format(topic, str(payload)))
#    mqtt_publish( topic, payload )

#==========================================
def main():
  logging.basicConfig()
  if cfg['DEBUG'] == True:
    logging.getLogger().setLevel(logging.DEBUG)
  logging.info("Starting")

  mqttclient = mqtt_start()
  api = MTECapi.MTECapi()
  stations = api.getStations()

  while True:
    for station_id, station_data in stations:
      devices = api.getDevices(station_id)
      pvdata = read_MTEC_station_data(api, station_id)
      base_topic = cfg['MQTT_TOPIC'] + '/' + station_data['name'] + '/'
      write_to_MQTT( pvdata, base_topic )
      for device_id, device_data in devices: 
        pvdata = read_MTEC_device_data(api, device_id)
        base_topic = cfg['MQTT_TOPIC'] + '/' + station_data['name'] + '/' + device_data['name'] + '/'
        write_to_MQTT( pvdata, base_topic )

    logging.debug("Sleep {}s".format( cfg['POLL_FREQUENCY'] ))
    time.sleep(cfg['POLL_FREQUENCY'])

  mqtt_stop(mqttclient)
  logging.info("Stopped")

if __name__ == '__main__':
  main()
