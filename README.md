# EaseeLoadBalancer

This project reads the excess solar power via modbusTCP and sets the easee charger to charge acordingly.

As of now the project is compatible with Huawei Sun2000 inverters that have installed a network dongle and an Easee Charger.

EaseeLoadBalancer interfaces with the Huawei inverter and reads the following data on modbusTCP:
- Export power, from the smart meter
- Solar production
- Battery Charge Power
- Battery SOC

EaseeLoacBalancer interfaces with the Easee Charger with their public API. This is used to do serveral things but most importantly is getting the actual charge power to calculate the new setpoint.

The formula for setting the charge power is the following:
newSp = carCharge + export + batteryCharge


Guide:

1.  Activating ModbusTCP(installer account only)
Follow this guide: https://forum.huawei.com/enterprise/en/modbus-tcp-guide/thread/789585-100027

2.  Installing python
install python on the device you intend to use. There are serveral guides to do this on the internet. I reccoment to get Visual Studio Code for this untill you are up and running.

3.  Download EaseeLoadBalancer
Download the EaseeLoadBalancer.py and open it in your prefered texteditor(VS Code).

4.  Change program parameters to your own
To use the program at your site you need to change the following parameters in the top
![image](https://user-images.githubusercontent.com/7197181/196762740-3fb3c0ef-3299-46db-8aea-d2b138be7350.png)


- CHARGER_ID = see picture
- SITE_ID = see picture
- CIRCUIT_ID = see step 5
- USERNAME = the same you use for logging in to your easee.cloud account
- PASSWORD = the same you use for logging in to your easee.cloud account
- INVERTER_IP = '192.168.x.x'the ip that your Sun2000 inverte has on your local network. I reccomend setting a static ip in your router
- INVERTER_PORT = 502           #<------- should be 502
Charger and SiteId can be found by logging in to easee.cloud. There you can find your ChargerID under "Products" pane
![image](https://user-images.githubusercontent.com/7197181/196766935-a1aa9b99-668e-4404-97b6-ca071ec91f66.png)

5.
To obtain the CircuitID we need to use the API. An API is an Application Programming Interface. Its just a way of enabling programs to communicate with other programs. As we are doing in this case.

5.1
In order to retrieve the CircuitId we need to "log in" and get a token. A token is just a very complex string the api returns upon logging in. This "Token" is used instead of our login cridentials. This is done to security reasons.

Go to Easees API under Account/Authentication: https://developer.easee.cloud/reference/post_api-accounts-login
  1 and 2. input your username and password.
  3. write "Bearer ".   Remember capital B and the space
  4. Try it. you should receive some json code
  5. grab the token and save it in a text editor.
  ![image](https://user-images.githubusercontent.com/7197181/196770468-e2e49228-6090-45d5-90ad-6e420be97d21.png)
  7. input it in the Authentication field. it should look like this:
  ![image](https://user-images.githubusercontent.com/7197181/196771354-3274acf2-bd69-451a-b63f-f7a1a7d9f08b.png)

5.3 Get site
Go to Easees API under Site/Get Site:  https://developer.easee.cloud/reference/getsitebyid
  1. input the siteId we got earlier by logging into Easee.Cloud
  2. make sure detailed is set to True
  3. press try it
  ![image](https://user-images.githubusercontent.com/7197181/196772350-dca19b13-1e25-43ab-8d4c-2eb8742e83d6.png)
  5. it should return a long piece of JSON. on line 37 you should find the CircuitId
  ![image](https://user-images.githubusercontent.com/7197181/196772532-1f3fd74e-c6e5-4e6e-9494-7e51c65822d6.png)
  7. open EaseeLoadBalancer.py and input the value we just found.

6.
we should now be able to run the program.
When the rogramming is running you can see the logged and calculated data each time the program publishes new charge power to the charger.

![image](https://user-images.githubusercontent.com/7197181/196727816-9e2dd127-b4c4-4b43-bf59-671239491eee.png)
