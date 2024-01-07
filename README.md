# M-TEC API
Welcome to the `M-TEC API` project!
It enables to read data from a M-TEC Energybutler system (https://www.mtec-systems.com) using the M-TEC online service.

Hint: It you are looking for a project which enables to read the M-TEC Inverter directly and without Internet, have a look at my `MTECmqtt` project! 

The trigger for this project was, that after my PV inverter from M-TEC was installed, I wanted to read out some data and statistics in order to integrate it into my smart home environment. Unfortunately, I couldn't find any documented API to access the M-TEC inverter. 
Luckily, there is a quite nice Web-portal available at https://energybutler.mtec-portal.com. The Web UI uses a REST API to retrieve data from a backend, which is "magically" fed by the inverter. (It could be worth another project, to find out more about how this works...).

I decided to have a closer look at this REST API. And here we are! This project is the result of that endeavour to reverse-engineer that API. 

I hope you can make use of it and adapt it to your use-cases.

## Remarks
During I started developing this project in March 2023, MTEC seems to be doing some refactoring and updating of their portal, application and API. 

Therefore e.g. Daily consumption values are only available starting 07.03.2023. 

I will try to keep track of these changes - also in my own interest. ;-) 
In order not to do uninteneded changes or settings and avoid any side-effects, I intentionally implemented read functionality only. 

_Disclaimer:_ This project is a pure hobby project which I created by reverse-engineering the M-TEC Web-portal. It is *not* related to or supported by M-TEC GmbH by any means. Usage is on you own risk. I don't take any responsibility on functionality or potential damage.

## What it offers
### API
The actual API can be found in `MTECapi.py`. It offers functionality to:
* Connect to yout M-TEC account
* List your Plants and Devices and their base data
* Retrieve current status and usage data
* Retrieve historical usage data with different aggregation levels (day, month)

### Demo client
The demo-client `MTEC_client.py` is a simple interactive tool which makes use of `MTECapi` class and shows how to use it.

### CSV export tool
The command-line tool `export_data.py` offers functionality to export usage data in CSV format.
This enables to archive the data localy or to process it further in a database or spreadsheet tool.   

### MQTT server
The MQTT server `MTEC_mqtt.py` enables to export station and/or device data to a MQTT broker. This can be useful, if you want to use the data e.g. as source for an EMS or home automation tool. Many of them enable to read data from MQTT, therefore this might be a good option for an easy integration.

### Tools and utils
#### cronjob
I wanted to have a daily export of the PV data and store it on a lokal NAS drive.
Therefore I wrote a little shell script which uses the CSV export tool and saved the data on a NFS mounted drive. It is called `cron_daily.sh`.
You probably need to adjust some paths to make it fit to your environment.

If you want to add it to the crontab, you need to open your crontab with `crontab -e` and add a line like e.g. 
```
0 5 * * * /home/pi/MTEC_API/cron_daily.sh 2>&1 /home/pi/MTEC_API/cron.log
```

#### NFS mount 
In `templates` you find a systemctl file which enables to NFS mount a drive from a local NAS (`mnt-public.mount`).
You just might need to replace some minor things like hostname/IP addresses etc.

_Hint:_ In order to install it, you need to be root (or use sudo):

- Copy it to the systemd directory `/etc/systemd/system`
- Reload systemctl units by `systemctl daemon-reload`
- To start a service manually, use `systemctl start mnt-public.mount` etc. 
- To start a service at boot time automatically, use `systemctl enable mnt-public.mount` etc.

## Setup & configuration

As prerequisites, you need to have installed Python 3 and https://pypi.org/project/PyYAML/.
(Depending on your Python installation, installation might require root rights or using `sudo`)

PyYAML can be installed easily like this:

```
pip3 install pyyaml
```

Now download the files of *this* repository to any location of your choise.
Then copy `config.yaml` from the `templates` directory to the project root (=same directory where `MTECapi.py` is locaed).

Without any further configuration, `MTECapi` will use the demo-account which is offered on the official M-TEC Web-portal.

In order to connect to your individual device, you need to provide the credentials you used to register your device within the M-TEC protal and add them to `config.yaml`.

```
PV_EMAIL : ""               # e-mail address you used to register at M-TEC portal
PV_PASSWORD : ""            # password you used to register at M-TEC portal
```

## Demo client
Having done the setup, you already should be able to start the demo-client `MTEC_client.py`.
It will show you a menu where you can choose from several options:

```
Menu:
  1: List system topology
  2: List station data
  3: List device data
  4: Usage data (day)
  5: Usage data (month)
  x: Exit
Please select:
```

## CSV export tool
The command-line tool `export_data.py` offers functionality to export historical usage data in CSV format.
This enables to archive the data localy or to process it further in a database or spreadsheet tool.

You can choose between "day", "month", "year" or "lifetime" data. 

## MQTT server
The MQTT server `MTEC_mqtt.py` enables to export station and/or device data to a MQTT broker. This can be useful, if you want to use the data e.g. as source for an EMS or home automation tool. Many of them enable to read data from MQTT, therefore this might be a good option for an easy integration.

### Configuration
Please see following options in `config.yaml` to configurate the service according your demand:

```
# MQTT
MQTT_SERVER : "localhost"   # MQTT server 
MQTT_PORT : 1883            # MQTT server port
MQTT_LOGIN  : " "           # MQTT Login
MQTT_PASSWORD : ""          # MQTT Password  
MQTT_TOPIC : "MTEC"         # MQTT topic name (top-level)  

POLL_FREQUENCY : 60         # query data every N seconds
DEBUG : False               # Set to True to get verbose debug messages
WRITE_STATION_DATA : True   # Choose if you want to write station data to MQTT
WRITE_DEVICE_DATA : True    # Choose if you want to write device data to MQTT

MQTT_FLOAT_FORMAT : "{:.2f}"    # Defines how to format float values 
```

### Data format written to MQTT

The script will login with the given M-TEC credentials and will auto-detect the topology of your plant. It will then loop over all existing stations and all the devices within each station. It will write the data to MQTT every `POLL_FREQUENCY` seconds. 

If `WRITE_STATION_DATA` is set to True, the station specific data will be written to a MQTT topic, using following naming:

`MTEC/<station_name>/<parameter>`

| Parameter             | Type  | Unit | Description 
|---------------------- | ----- | ---- | ---------------------------------------------- 
| day_production        | float | kWh  | Energy produced by the PV today 
| month_production      | float | kWh  | Energy produced by the PV this month
| year_production       | float | kWh  | Energy produced by the PV this year
| total_production      | float | kWh  | Energy produced by the PV in total
| current_PV            | float | W    | Current flow from PV
| current_grid          | float | W    | Current flow from/to grid (feed in to grid is represented by neg. values)
| current_battery       | float | W    | Current flow from/to battery (feed in to battery is represented by neg. values)
| current_battery_SOC   | int   | %    | Current battery SOC
| current_load          | float | W    | Current consumed energy
| grid_interrupt        | int   |      | 0=Grid connected, 1=Grid interrupted 

If `WRITE_DEVICE_DATA` is set to True, the device specific data will be written to a MQTT topic, using following naming:

`MTEC/<station_name>/<device_name>/<parameter>`

| Parameter             | Type  | Unit  | Description
|---------------------- | ----- | ---- | ---------------------------------------------- 
| battery_P             | float | W    | Battery power             
| battery_V             | float | V    | Battery voltage
| battery_I             | float | A    | Battery current
| battery_SOC           | float | %    | Battery state of charge
| inverter_A_P          | float | W    | Inverter phase L1 power
| inverter_A_V          | float | V    | Inverter phase L1 voltage
| inverter_A_I          | float | A    | Inverter phase L1 current
| inverter_B_P          | float | W    | Inverter phase L2 power
| inverter_B_V          | float | V    | Inverter phase L2 voltage
| inverter_B_I          | float | A    | Inverter phase L2 current
| inverter_C_P          | float | W    | Inverter phase L3 power
| inverter_C_V          | float | V    | Inverter phase L3 voltage
| inverter_C_I          | float | A    | Inverter phase L3 current
| grid_A_P              | float | W    | Grid phase L1 power
| grid_B_P              | float | W    | Grid phase L2 power
| grid_C_P              | float | W    | Grid phase L3 power
| PV_PV1_P              | float | W    | PV string 1 power
| PV_PV1_V              | float | V    | PV string 1 voltage
| PV_PV1_I              | float | A    | PV string 1 current
| PV_PV2_P              | float | W    | PV string 2 power
| PV_PV2_V              | float | V    | PV string 2 voltage
| PV_PV2_I              | float | A    | PV string 2 current

The existance of the latter parameters (`PV_PVx_...`) depend on the no. of installed PV strings (typically 1 or 2). 

All `float` values will be written according to the configured `MQTT_FLOAT_FORMAT`. The default is a format with 2 decimal digits. 
