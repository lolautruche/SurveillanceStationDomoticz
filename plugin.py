# Synology SurveillanceStation plugin for Domoticz
#
# Author: Jerome Vieilledent
#
"""
<plugin key="SurveillanceStation" name="Synology SurveillanceStation plugin" author="lolautruche" version="0.1">
    <description>
        <h2>Synology SurveillanceStation plugin for Domoticz</h2><br/>
        Gives an access to SurveillanceStation API
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Toggle "Home Mode"</li>
        </ul>
        <h3>Devices</h3>
        <ul style="list-style-type:square">
            <li>HomeMode switch - Toggles Home mode...</li>
        </ul>
    </description>
    <params>
        <param field="Address" label="SurveillanceStation address (without http://)" required="true" default="127.0.0.1"/>
        <param field="Mode1" label="Protocol">
            <options>
                <option label="HTTP" value="HTTP" default="true"/>
                <option label="HTTPS" value="HTTPS"/>
            </options>
        </param>
        <param field="Port" label="Port" required="true" default="5000"/>
        <param field="Mode2" label="SurveillanceStation User" required="true"/>
        <param field="Mode3" label="Password" required="true"/>
    </params>
</plugin>
"""
import Domoticz
import json

class BasePlugin:
    SurvStationConn = None
    SurvStationSid = None
    APIPaths = {
        'SYNO.API.Info': 'query.cgi',
        'SYNO.API.Auth': 'auth.cgi',
        'SYNO.SurveillanceStation.HomeMode': 'entry.cgi'
    }
    APIURLs = {
        'SYNO.API.Info.Query': '/webapi/%(path)s.cgi?api=SYNO.API.Info&method=Query&version=1&query=SYNO.API.Auth,SYNO.SurveillanceStation.HomeMode',
        'SYNO.API.Auth.Login': '/webapi/%(path)s?api=SYNO.API.Auth&method=Login&version=2&account=%(username)s&passwd=%(password)s&session=SurveillanceStation&format=sid',
        'SYNO.API.Auth.Logout': '/webapi/%(path)s?api=SYNO.API.Auth&method=Logout&version=2&session=SurveillanceStation&_sid="%(sid)s"',
        'SYNO.SurveillanceStation.HomeMode.Switch': '/webapi/%(path)s?api=SYNO.SurveillanceStation.HomeMode&method=Switch&version=1&on=%(on_status)s&_sid="%(sid)s"',
        'SYNO.SurveillanceStation.HomeMode.GetInfo': '/webapi/%(path)s?api=SYNO.SurveillanceStation.HomeMode&method=GetInfo&version=1&_sid="%(sid)s"'
    }
    LastCalledAPI = None
    LastCalledParams = None
    HeartBeatsCount = 6

    def onStart(self):
        Domoticz.Debugging(1)

        if (len(Devices) == 0):
            Domoticz.Device(Name="HomeMode", Unit=1, Type=244, Switchtype=0).Create()

        self.SurvStationConn = Domoticz.Connection(Name="SurvStationConn", Transport="TCP/IP", Protocol=Parameters["Mode1"], Address=Parameters["Address"], Port=Parameters["Port"])
        self.SurvStationConn.Connect()

    def onStop(self):
        Domoticz.Log("Logging out from ServeillanceStation")
        self._logout()

    def onConnect(self, Connection, Status, Description):
        Domoticz.Log("Status: "+str(Status))
        Domoticz.Log(Description)
        if (Status != 0):
            Domoticz.Log("Failed to connect ("+str(Status)+") to: "+Connection.Address+":"+Connection.Port)
            Domoticz.Debug("Failed to connect ("+str(Status)+") to: "+Connection.Address+":"+Connection.Port+" with error: "+Description)

        self._queryAPI('SYNO.API.Info', 'Query')

    def _queryAPI(self, APIName, Method, Params={}):
        if (APIName not in self.APIPaths):
            Domoticz.Log("API '"+APIName+"' not currently supported by plugin")
            return

        Params['path'] = self.APIPaths[APIName]
        APIMethod = APIName+'.'+Method
        # Auth.Login and Info don't need SID
        if (APIMethod != 'SYNO.API.Auth.Login') and (APIName != 'SYNO.API.Info'):
            Params['sid'] = self.SurvStationSid

        URL = self.APIURLs[APIMethod] % Params
        Domoticz.Log(URL)
        self.SurvStationConn.Send({
            'Verb': 'GET',
            'URL': URL,
            'Headers': {'Host': Parameters['Address']+':'+Parameters['Port']}
        })
        self.LastCalledAPI = APIMethod
        self.LastCalledParams = Params

    def _login(self):
        self._queryAPI('SYNO.API.Auth', 'Login', {'username': Parameters['Mode2'], 'password': Parameters['Mode3']})

    def _logout(self):
        self.SurvStationSid = None
        self._queryAPI('SYNO.API.Auth', 'Logout')

    def onMessage(self, Connection, Data):
        strData = Data["Data"].decode("utf-8", "ignore")
        Domoticz.Log(strData);
        response = json.loads(strData);

        if ("error" in response):
            Domoticz.Log("An error was raised by SurveillanceStation API!")
            if (response["error"]["code"] == 100):
                Domoticz.Log("Unknown error")
            elif (response["error"]["code"] == 104):
                Domoticz.Log("This API version is not supported")
            elif (response["error"]["code"] == 105):
                Domoticz.Log("Insufficient user privilege")
                self.SurvStationSid = None
                self._login()
                # TODO: Replay last API call
            elif (response["error"]["code"] == 107):
                Domoticz.Log("Multiple login detected")
        elif (self.LastCalledAPI == 'SYNO.API.Info.Query'): # Getting API paths
            for name, info in response['data'].items():
                self.APIPaths[name] = info["path"]
            # Authenticate if needed
            if (self.SurvStationSid == None):
                self._login()
        elif (self.LastCalledAPI == 'SYNO.API.Auth.Login'):
            Domoticz.Log("Authenticated with session ID "+response["data"]["sid"])
            self.SurvStationSid = response["data"]["sid"]
        elif (self.LastCalledAPI == 'SYNO.SurveillanceStation.HomeMode.GetInfo'):
            Domoticz.Log("Updating HomeMode status: "+str(response["data"]["on"]))
            nValue = 0
            sValue = 'Off'
            if (response["data"]["on"] == True):
                nValue = 1
                sValue = 'On'
            UpdateDevice(1, nValue, sValue)

    def onCommand(self, Unit, Command, Level, Color):
        Domoticz.Log("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        # onCommand called for Unit 1: Parameter 'Off', Level: 0
        if (Unit == 1):
            Params = {'on_status': 'true' if Command == 'On' else 'false'}
            Level = 1 if Command == 'On' else 0
            self._queryAPI('SYNO.SurveillanceStation.HomeMode', 'Switch', Params)

        UpdateDevice(Unit, Level, Params)

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        #Domoticz.Log("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)
        return

    def onDisconnect(self, Connection):
        Domoticz.Log(Connection.Name+" was disconnected")
        self.SurvStationSid = None
        return

    def onHeartbeat(self):
        self.HeartBeatsCount = self.HeartBeatsCount - 1
        # API call every 6 heartbeats (~1 min)
        if (self.HeartBeatsCount <= 0):
            self.HeartBeatsCount = 6
            self._queryAPI('SYNO.SurveillanceStation.HomeMode', 'GetInfo')

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

### Generic helper functions
def UpdateDevice(Unit, nValue, sValue):
    # Make sure that the Domoticz device still exists (they can be deleted) before updating it
    if (Unit not in Devices):
        return

    if (Devices[Unit].nValue != nValue) or (Devices[Unit].sValue != sValue):
        Devices[Unit].Update(nValue=nValue, sValue=str(sValue))
        Domoticz.Log("Update "+str(nValue)+":'"+str(sValue)+"' ("+Devices[Unit].Name+")")
    return

def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def DumpHTTPResponseToLog(httpDict):
    if isinstance(httpDict, dict):
        Domoticz.Debug("HTTP Details ("+str(len(httpDict))+"):")
        for x in httpDict:
            if isinstance(httpDict[x], dict):
                Domoticz.Debug("--->'"+x+" ("+str(len(httpDict[x]))+"):")
                for y in httpDict[x]:
                    Domoticz.Debug("------->'" + y + "':'" + str(httpDict[x][y]) + "'")
            else:
                Domoticz.Debug("--->'" + x + "':'" + str(httpDict[x]) + "'")
