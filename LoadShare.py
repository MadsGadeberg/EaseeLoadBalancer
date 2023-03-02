from cmath import phase
from pyModbusTCP.client import ModbusClient
import requests
import threading
import time
from datetime import datetime

PULL_DATA_RETRIES = 3
BROADCAST_CHARGE_DELAY = 5
TIME_TO_LIVE = 1    
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
        response = ""
        try:
            response = requests.post(url, data=payload, headers=headers).json()
        except:
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
        thread = threading.Timer(BROADCAST_CHARGE_DELAY, self.broadcastChargeCurrent).start()

        if threading.active_count() < 4:
            export = self.inverter.getExport()
            batterySOC = self.inverter.getSOC()
            batteryCharge = self.inverter.getBatCharge()
            carCharge = self.easeeCharger.getChargePower()

            if None not in (export, carCharge, batteryCharge, batterySOC):
                
                excessPowerTot  = carCharge + export + batCharge    # surplus power including battery charge
                SP = 0
                
                if batSOC >= 100:
                    self.mode = 0     # favour Car charging / discharge house battery
                #elif batSOC >= 80:
                #    self.mode = 2     # favour house battery but only a little
                elif batSOC < 80:
                    self.mode = 1     # favour house battery charging
                      
                if self.mode == 1:
                    # this mode favors charging the battery with little excess power
                    if excessPowerTot < 5:
                        SP = 0
                    elif 5 < excessPowerTot < (5+4.2):
                        #SP = 1.4 ## 1 phase charging needs implementing before this works
                        SP = 4.2
                    elif (5+4.2) < excessPowerTot:
                        SP = excessPowerTot - 5
                elif self.mode == 0:
                    # this mode discharges battery if there is little underksud in export.
                    if 0 < excessPowerTot < 1.4:
                        #SP = 1.4 ## 1 phase charging needs implementing before this works
                        
                        SP = 4.2
                    elif 1.4 < excessPowerTot < 3.7:
                        #SP = excessPowerTot # 1 phase      ## 1 phase charging needs implementing before this works
                        SP = 4.2
                    elif 3.7 < excessPowerTot < 4.2:
                        SP = excessPowerTot # last phase setting to avoid phase setting changes
                        #SP = excessPowerTot # 1 phase      ## 1 phase charging needs implementing before this works
                        SP = 4.2
                    elif 4.2 < excessPowerTot:
                        SP = excessPowerTot + 0.5 # 3 phases
                elif self.mode == 2:
                    # this mode favors charging the battery with little excess power
                    if excessPowerTot < 5:
                        SP = 0
                    elif 5 < excessPowerTot < (5+4.2):
                        #SP = 1.4 ## 1 phase charging needs implementing before this works
                        SP = excessPowerTot - 0.5
                    elif (5+4.2) < excessPowerTot:
                        SP = excessPowerTot - 0.5
                      
                if SP < 0:
                    SP = 0
                elif SP > 11.1:
                    SP = 11.1
                
                chargeAmp = SP * 1.45
                
                self.easeeCharger.setCurrent(chargeAmp, TIME_TO_LIVE)

                print("-----------------------")
                print("Mode:            " + "{:.0f}".format(self.mode))
                print("EPT:             " + "{:.2f}kW".format(excessPowerTot))
                print("export:          " + "{:.2f}kW".format(export))
                print("CarCharge:       " + "{:.2f}kW".format(carCharge))
                print("batSOC:          " + "{:.0f}%".format(batSOC))
                print("batCharge:       " + "{:.2f}kW".format(batCharge))
                print("SP:              " + "{:.2f}kW".format(SP))
                print("chargeAmp:       " + "{:.2f}A".format(chargeAmp))

            else:
                if export == None:
                    print("export timeout")
                elif carCharge == None:
                    print("CarCharge timeout")
                elif batCharge == None:
                    print("batCharge timeout")
                elif batSOC == None:
                    print("batSOC timeout")
        else:
            print("Prior thread didnt execute:     " + str(threading.active_count()))

loadBalancer = LoadBalancer()
#loadBalancer.easeeCharger.setPhases(3)
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
