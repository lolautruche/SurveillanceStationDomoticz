# Synology SurveillanceStation plugin for Domoticz

Gives an access to SurveillanceStation Web API.

## Features
- Handles authentication.
- Toggles `HomeMode` with a dedicated switch (note that by default when `HomeMode` is activated, cameras will record).
- Polls `HomeMode` status, in case it was toggled from outside Domoticz.

## Requirements
- Python 3.4 (3.5 recommended)
- Domoticz 4.10717 (only tested version, may work on previous versions)
- Git (if you install the plugin from git)

## Install
- With a terminal, navigate to Domoticz plugin directory (`plugins/` folder under Domoticz main directory)
  - Plugins folder may be under `domoticz/var/` folder (i.e. when installed on a Synology NAS)
- Clone with Git: `git clone https://github.com/lolautruche/SurveillanceStationDomoticz.git`
- Restart Domoticz service (e.g. `sudo service domoticz.sh restart`

## Update
- With a terminal, navigate to SurveillanceStationDomoticz plugin directory (`domoticz/plugins/SurveillanceStationDomoticz`)
- Launch following command: `git pull`
- Restart Domoticz service (e.g. `sudo service domoticz.sh restart`)


## Configuration
In Settings/Hardware, add a new hardware of type `Synology SurveillanceStation plugin`

| Field | Information|
| ----- | ---------- |
| SurveillanceStation address | IP address or domain name of your Synology SurveillanceStation server (without `http`)  |
| Protocol | Choose either `HTTP` or `HTTPS` depending on how you access to SurveillanceStation |
| Port | Port to use to access to SurveillanceStation |
| SurveillanceStation User | User to use for authentication. **It's recommended to create a dedicated user in SurveillanceStation**. This user needs to have access to `HomeMode` |
| Password | Password for the user |
| Debug | If true, more information will be dumped into the log |
