from pickle import TRUE
from pyModbusTCP.client import ModbusClient
import requests
import threading
import datetime
import time
from datetime import datetime


PRINT_TIME = 1
BROADCAST_CHARGE_DELAY = 3
TIME_TO_LIVE = 1
CHARGER_ID = "EH49EDUN"                                             #<----------change
SITE_ID = 133063                                                    #<----------change
CIRCUIT_ID = 128434                                                 #<----------change
USERNAME = "username"                                               #<----------change
PASSWORD = "password"                                               #<----------change
INVERTER_IP = '192.168.1.6'                                         #<----------change
INVERTER_PORT = 502

class Inverter():
    c = ModbusClient(host=INVERTER_IP, port=INVERTER_PORT, unit_id=1, timeout = 3,debug=False, auto_open=True, auto_close=False)

    production = 0
    export = 0
    batSOC = 0
    batCharge = 0
    
    def getExport(self):
        if not self.c.is_open:
            try:
                self.c.open()
            except:
                return None
            else:
                time.sleep(1)
        elif self.c.is_open:
            try:
                #   "power_meter_active_power": RegisterDefinitions("i32", "W", 1, 37113, 2),
                export = int.from_bytes(self.c.read_holding_registers(37113, 2)[1].to_bytes(2, 'big'), byteorder='big', signed = True)/1000
            except:
                return None
            else:
                return export

    def getSOC(self):
        if not self.c.is_open:
            try:
                self.c.open()
            except:
                return None
            else:
                time.sleep(1)
        elif self.c.is_open:
            try:
                #   "power_meter_active_power": RegisterDefinitions("i32", "W", 1, 37113, 2),
                batSOC = self.c.read_holding_registers(37004, 2)[0] / 10
            except:
                return None
            else:
                return batSOC

    def getBatCharge(self):
        if not self.c.is_open:
            try:
                self.c.open()
            except:
                return None
            else:
                time.sleep(1)
        elif self.c.is_open:
            try:
                #   "power_meter_active_power": RegisterDefinitions("i32", "W", 1, 37113, 2),
                batCharge = int.from_bytes(self.c.read_holding_registers(37001, 2)[1].to_bytes(2, 'big'), byteorder='big', signed = True)/1000
            except:
                return None
            else:
                return batCharge

    def getProduction(self):
        if not self.c.is_open:
            try:
                self.c.open()
            except:
                return None
            else:
                time.sleep(1)
        elif self.c.is_open:
            try:
                #   "power_meter_active_power": RegisterDefinitions("i32", "W", 1, 37113, 2),
                result = self.c.read_holding_registers(32064, 2)[1]/1000
            except:
                return None
            else:
                return result


    # method service that is executed every "SAMPLE_TIME"
    def getData(self):
        self.c.open()
        time.sleep(1)
            
        #RegisterDefinitions = namedtuple( "RegisterDefinitions", "type unit gain register length" )
        ##  get all data
        #   "grid_current": RegisterDefinitions("i32", "A", 1000, 32072, 2),
        #   "phase_A_current": RegisterDefinitions("i32", "A", 1000, 32072, 2),
        #   "phase_B_current": RegisterDefinitions("i32", "A", 1000, 32074, 2),
        #   "phase_C_current": RegisterDefinitions("i32", "A", 1000, 32076, 2),
        #   "input_power": RegisterDefinitions("i32", "W", 1, 32064, 2),
        self.production = self.c.read_holding_registers(32064, 2)[1]/1000
        #   "storage_unit_1_running_status": RegisterDefinitions("u16", "storage_running_status_enum", 1, 37000, 1),
        #   "storage_unit_1_charge_discharge_power": RegisterDefinitions("i32", "W", 1, 37001, 2),
        #self.batCharge = self.c.read_holding_registers(37001, 2)[1]
        self.batCharge = int.from_bytes(self.c.read_holding_registers(37001, 2)[1].to_bytes(2, 'big'), byteorder='big', signed = True)/1000
        #   "storage_unit_1_state_of_capacity": RegisterDefinitions("u16", "%", 10, 37004, 1),
        self.batSOC = self.c.read_holding_registers(37004, 2)[0] / 10
        #   "storage_unit_1_battery_pack_1_state_of_capacity": RegisterDefinitions(        "u16", "%", 10, 38229, 1
        #   "meter_status": RegisterDefinitions("u16", "meter_status_enum", 1, 37100, 1),

        #   "meter_type": RegisterDefinitions("u16", "meter_type_enum", 1, 37125, 2),  

        self.c.close()

class EaseeCharger():
    token = ""
    refreshToken = ""
    carCharge = 0
    chargePower = 0

    def login(self, userName, password):
        url = "https://api.easee.cloud/api/accounts/login"

        payload = "{\"userName\":\"" + userName + "\",\"password\":\"" + password + "\"}"
        headers = {
            "accept": "application/json",
            "content-type": "application/*+json"
        }

        response = requests.post(url, data=payload, headers=headers).json()
        self.token = response["accessToken"]
        self.refreshToken = response["refreshToken"]
    
    def refreshTokenn(self):
        url = "https://api.easee.cloud/api/accounts/refresh_token"

        payload = "{\"refreshToken\":\"" + self.refreshToken + "\",\"accessToken\":\"" + self.token + "\"}"
        headers = {
            "accept": "application/json",
            "content-type": "application/*+json",
            "Authorization": "Bearer " + self.token
        }

        response = requests.post(url, data=payload, headers=headers).json()
        self.token = response["accessToken"]
        self.refreshToken = response["refreshToken"]

    def getCurrent(self):
        url = "https://api.easee.cloud/api/sites/" + str(SITE_ID) + "/circuits/" + str(CIRCUIT_ID) + "/dynamicCurrent"

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + self.token
        }

        response = requests.get(url, headers=headers)
        print(response.text)

    def setCurrent(self, chargeAmp, timeToLive):
        url = "https://api.easee.cloud/api/sites/" + str(SITE_ID) + "/circuits/" + str(CIRCUIT_ID) + "/dynamicCurrent"
        print(str(chargeAmp))
        payload = "{\"phase1\":" + str(chargeAmp) + ",\"phase2\":" + str(chargeAmp) +",\"phase3\":" + str(chargeAmp) + ",\"timeToLive\":" + str(timeToLive) + "}"
        headers = {
            "content-type": "application/*+json",
            "Authorization": "Bearer " + self.token
        }

        response = requests.post(url, data=payload, headers=headers).json()
        print(response)
    def getState(self):

        url = "https://api.easee.cloud/api/chargers/" + str(CHARGER_ID) + "/state"

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + self.token
        }

        try:
            response = requests.get(url, headers=headers).json()
        except:
            print("error getting state")
        else:
            self.actualVoltageL1 = response["inVoltageT2T3"]
            self.actualVoltageL2 = response["inVoltageT2T4"]
            self.actualVoltageL3 = response["inVoltageT2T5"]
            self.actualCurrentL1 = response["inCurrentT2T3"]
            self.actualCurrentL2 = response["inCurrentT2T4"]
            self.actualCurrentL3 = response["inCurrentT2T5"]

    def getChargePower(self):
        url = "https://api.easee.cloud/api/chargers/" + CHARGER_ID + "/state"

        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + self.token
        }

        try:
            response = requests.get(url, headers=headers).json()
        except:
            #print("error getting chargePower")
            return None
        else:
            return response["totalPower"]

class LoadBalancer():
    inverter = Inverter()
    easeeCharger = EaseeCharger()

    def start(self):
        self.easeeCharger.login(USERNAME, PASSWORD)
        self.broadcastChargeCurrent()

    def broadcastChargeCurrent(self):
        threading.Timer(BROADCAST_CHARGE_DELAY, self.broadcastChargeCurrent).start()
        
        export = self.inverter.getExport()
        production = self.inverter.getProduction()
        carCharge = self.easeeCharger.getChargePower()

        batterySOC = self.inverter.getSOC()
        batteryCharge = self.inverter.getBatCharge()

        if None not in (export, production, carCharge, batteryCharge):
            newSp = carCharge + export + batteryCharge
            newSp = 0 if newSp < 0 else 11 if newSp > 11 else newSp
            chargeAmp = newSp * 1.44
            self.easeeCharger.setCurrent(chargeAmp, TIME_TO_LIVE)

            print("-------------------------------------")
            print("production:          " + "{:.2f}kW".format(production))
            print("export:              " + "{:.2f}kW".format(export))
            print("actualCarCharge:     " + "{:.2f}kW".format(carCharge))
            #print("batSOC:              " + "{:.0f}%".format(batterySOC))
            print("batCharge:           " + "{:.2f}kW".format(batteryCharge))
            print("newSp:               " + "{:.2f}kW".format(newSp))
            print("newSpToCharger:      " + "{:.2f}kW".format(newSp))
        else:
            print("data read error")



loadBalancer = LoadBalancer()
loadBalancer.start()


# to do:
# - run get methods untill they return var - at least 3 times.
# - Validate the Statemethos has a timestamp that is only 1s old.
# - consider if we need to implement get state method to validate setpoint
