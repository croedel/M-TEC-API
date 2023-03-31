# M-TEC Energybutler API
Welcome to the `M-TEC Energybutler API` project!
It enables to read data from a M-TEC Energybutler system (https://www.mtec-systems.com).

The trigger for this project was, that after my PV inverter from M-TEC was installed, I wanted to read out some data and statistics in order to integrate it into my smart home environment. Unfortunately, I couldn't find any documented API to access the M-TEC inverter. 
Luckily, there is a quite nice Web-portal available at https://energybutler.mtec-portal.com. The Web UI uses a REST API to retrieve data from a backend, which is "magically" fed by the inverter. (It could be worth another project, to find out more about how this works...).

I decided to have a closer look at this REST API. And here we are! This project is the result of that endeavour to reverse-engineer that API. 

I hope you can make use of it and adapt it to your use-cases.

_Disclaimer:_ This project is a pure hobby project which I created by reverse-engineering the M-TEC Web-portal. It is *not* related to or supported by M-TEC GmbH by any means. Usage is on you own risk. I don't take any responsibility on functionality or potential damage.

## What it offers
### API
The actual API can be found in `MTECapi.py`. It offers functionality to:
* Connect to yout M-TEC account
* List your Plants and Devices and their base data
* Retrieve current usage data
* Retrieve historical usage data with different aggregation levels (day, month)

### Demo client
The demo-client `MTEC_client.py` is a simple interactive tool which makes use of `MTECapi` class and shows how to use it.

### CSV export tool
The command-line tool `export_data.py` offers functionality to export usage data in CSV format.
This enables to archive the data localy or to process it further in a database or spreadsheet tool.   

## Setup & configuration
Download the files of *this* repository to any location of your choise.
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

### CSV export tool
The command-line tool `export_data.py` offers functionality to export usage data in CSV format.
This enables to archive the data localy or to process it further in a database or spreadsheet tool.


