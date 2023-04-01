# M-TEC API
Welcome to the `M-TEC API` project!
It enables to read data from a M-TEC Energybutler system (https://www.mtec-systems.com).

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

### Tools and utils
#### cronjob
I wanted to have a daily export of the PV data and store it on a lokal NAS drive.
Therefore I wrote a little shell script which uses the CSV export tool and saved the data on a NFS mounted drive. It is called `cron_daily.sh`.
You probably need to adjust some paths to make it fit to your environment.

If you want to add it to the crontab, you need to open your crontab with `crontab -e` and add a line like e.g. 
```
0 5 * * * /home/pi/infotainment/MTEC_energybutler_API/cron_daily.sh 2>&1 /home/pi/infotainment/MTEC_energybutler_API/cron.log
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


