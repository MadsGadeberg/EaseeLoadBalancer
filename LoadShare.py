from cmath import phase
from pyModbusTCP.client import ModbusClient
import requests
import threading
import time
from datetime import datetime

PULL_DATA_RETRIES = 10
BROADCAST_CHARGE_DELAY = 10
TIME_TO_LIVE = 3600
REFRESH_TOKEN = 43200 # 12h
CHARGER_ID = "EH49EDUN"                     #<------- Change to your own
SITE_ID = 133063                            #<------- Change to your own
CIRCUIT_ID = 128434                         #<------- Change to your own
USERNAME = "username"                       #<------- Change to your own
PASSWORD = "password"                       #<------- Change to your own
INVERTER_IP = '192.168.1.6'                 #<------- Change to your own
INVERTER_PORT = 502                         #<------- Change to your own

class Inverter():
    c = ModbusClient(host=INVERTER_IP, port=INVERTER_PORT, unit_id=1, timeout = 3,debug=False, auto_open=True, auto_close=False)

    
    def getExport(self):
        if not self.c.is_open:
            try:
                self.c.open()
            except:
                return None
            else:
                time.sleep(1)
        elif self.c.is_open:
            result = None
            tries = 0
            while result is None and tries <= PULL_DATA_RETRIES:
                try:
                    #   "power_meter_active_power": RegisterDefinitions("i32", "W", 1, 37113, 2),
                    result = int.from_bytes(self.c.read_holding_registers(37113, 2)[1].to_bytes(2, 'big'), byteorder='big', signed = True)/1000
                except:
                    result = None
                    tries += 1
                else:
                    return result
            self.c.close()
            return result

    def getSOC(self):
        if not self.c.is_open:
            try:
                self.c.open()
            except:
                return None
            else:
                time.sleep(1)
        elif self.c.is_open:
            result = None
            tries = 0
            while result is None and tries <= PULL_DATA_RETRIES:
                try:
                    #   "power_meter_active_power": RegisterDefinitions("i32", "W", 1, 37113, 2),
                    result = self.c.read_holding_registers(37004, 2)[0] / 10
                except:
                    result = None
                    tries += 1
                else:
                    return result
            self.c.close()
            return result

    def getBatCharge(self):
        if not self.c.is_open:
            try:
                self.c.open()
            except:
                return None
            else:
                time.sleep(1)
        elif self.c.is_open:
            result = None
            tries = 0
            while result is None and tries <= PULL_DATA_RETRIES:
                try:
                    #   "power_meter_active_power": RegisterDefinitions("i32", "W", 1, 37113, 2),
                    result = int.from_bytes(self.c.read_holding_registers(37001, 2)[1].to_bytes(2, 'big'), byteorder='big', signed = True)/1000
                except:
                    result = None
                    tries += 1
                else:
                    return result
            self.c.close()
            return result

    def getProduction(self):
        if not self.c.is_open:
            try:
                self.c.open()
            except:
                return None
            else:
                time.sleep(1)
        elif self.c.is_open:
            result = None
            tries = 0
            while result is None and tries <= PULL_DATA_RETRIES:
                try:
                    #   "power_meter_active_power": RegisterDefinitions("i32", "W", 1, 37113, 2),
                    result = self.c.read_holding_registers(32064, 2)[1]/1000
                except:
                    result = None
                    tries += 1
                else:
                    return result
            self.c.close()
            return result

class EaseeCharger():
    token = ""
    refreshToken = ""
    carCharge = 0
    chargePower = 0

    def login(self, userName, password):
        url = "https://api.easee.cloud/api/accounts/login"

        payload = "{\"userName\":\"" + USERNAME + "\",\"password\":\"" + PASSWORD + "\"}"
        headers = {
            "accept": "application/json",
            "content-type": "application/*+json"
        }

        response = requests.post(url, data=payload, headers=headers).json()
        self.token = response["accessToken"]
        self.refreshToken = response["refreshToken"]
    
    def refreshTokenn(self):
        threading.Timer(BROADCAST_CHARGE_DELAY, self.refreshTokenn).start()
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
        #print(response.text) use response to log command id to track process state

    def setCurrent(self, chargeAmp, timeToLive):
        url = "https://api.easee.cloud/api/sites/" + str(SITE_ID) + "/circuits/" + str(CIRCUIT_ID) + "/dynamicCurrent"
        
        payload = "{\"phase1\":" + str(chargeAmp) + ",\"phase2\":" + str(chargeAmp) +",\"phase3\":" + str(chargeAmp) + ",\"timeToLive\":" + str(timeToLive) + "}"
        headers = {
            "content-type": "application/*+json",
            "Authorization": "Bearer " + self.token
        }

        response = requests.post(url, data=payload, headers=headers).json()
        #print(response)
   
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

    def setPhases(self, phases):
        import requests

        url = "https://api.easee.cloud/api/chargers/" + CHARGER_ID + "/settings"

        payload = "{\"phaseMode\":" + str(phases) + "}"
        headers = {
            "content-type": "application/*+json",
            "Authorization": "Bearer " + self.token
        }

        response = requests.post(url, data=payload, headers=headers)

        print(response.text)

class LoadBalancer():
    inverter = Inverter()
    easeeCharger = EaseeCharger()

    def start(self):
        self.easeeCharger.login(USERNAME, PASSWORD)
        #self.easeeCharger.setPhases(1)
        self.broadcastChargeCurrent()

    def broadcastChargeCurrent(self):
        threading.Timer(BROADCAST_CHARGE_DELAY, self.broadcastChargeCurrent).start()
        
        export = self.inverter.getExport()
        production = self.inverter.getProduction()
        carCharge = self.easeeCharger.getChargePower()

        batterySOC = self.inverter.getSOC()
        batteryCharge = self.inverter.getBatCharge()

        if None not in (export, production, carCharge, batteryCharge, batterySOC):
            
            newSp = carCharge + export + batteryCharge

            if newSp < 0:
                newSp = 0
            elif newSp > 16:
                newSp = 16
            elif newSp < 4.2 and batterySOC > 90:
                newSp = 4.2

            #newSp = 0 if newSp < 0 else 11 if newSp > 11 else 4.2 if batterySOC > 90 else newSp
            
            chargeAmp = newSp * 1.44
            
            self.easeeCharger.setCurrent(chargeAmp, TIME_TO_LIVE)

            print("-----------------------")
            print("production:      " + "{:.2f}kW".format(production))
            print("export:          " + "{:.2f}kW".format(export))
            print("CarCharge:       " + "{:.2f}kW".format(carCharge))
            print("batSOC:          " + "{:.0f}%".format(batterySOC))
            print("batCharge:       " + "{:.2f}kW".format(batteryCharge))
            print("newSp:           " + "{:.2f}kW".format(newSp))
            print("chargeAmp:       " + "{:.2f}A".format(chargeAmp))

        else:
            print("-------------------------------------")
            print("production:      " + str(production))
            print("export:          " + str(export))
            print("CarCharge:       " + str(carCharge))
            print("batSOC:          " + str(batterySOC))
            print("batCharge:       " + str(batteryCharge))
            

loadBalancer = LoadBalancer()
loadBalancer.start()


# to do:
# - run get methods untill they return var - at least 3 times.
# - Validate the State method has a timestamp that is only 1s old.
# - consider if we need to implement get state method to validate setpoint
# - 1 phase charging to lower minimum charge power from 4,144kW to 1,4

#setChargePower
#    if chargepower < 4Kw i skift til 1 fase


        #RegisterDefinitions = namedtuple( "RegisterDefinitions", "type unit gain register length" )
        ##  get all data
        #   "grid_current": RegisterDefinitions("i32", "A", 1000, 32072, 2),
        #   "phase_A_current": RegisterDefinitions("i32", "A", 1000, 32072, 2),
        #   "phase_B_current": RegisterDefinitions("i32", "A", 1000, 32074, 2),
        #   "phase_C_current": RegisterDefinitions("i32", "A", 1000, 32076, 2),
        #   "input_power": RegisterDefinitions("i32", "W", 1, 32064, 2),
        #   "storage_unit_1_running_status": RegisterDefinitions("u16", "storage_running_status_enum", 1, 37000, 1),
        #   "storage_unit_1_charge_discharge_power": RegisterDefinitions("i32", "W", 1, 37001, 2),
        #   "storage_unit_1_state_of_capacity": RegisterDefinitions("u16", "%", 10, 37004, 1),
        #   "storage_unit_1_battery_pack_1_state_of_capacity": RegisterDefinitions(        "u16", "%", 10, 38229, 1
        #   "meter_status": RegisterDefinitions("u16", "meter_status_enum", 1, 37100, 1),
        #   "meter_type": RegisterDefinitions("u16", "meter_type_enum", 1, 37125, 2),
