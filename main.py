from rolling_appender_log import URollingAppenderLog, LogLevel
from pico_w_sensor_node import UPicoWSensorNode
import time

class AtmophericSensorNode(UPicoWSensorNode):
    
    #STATIC_NODE_RESTART_DELAY = 60               # Used to delay restraing main() on an unhandled exception
    STATIC_NODE_LOG_LEVEL = LogLevel.INFO       # Used to designate the log level required, normally LogLevel.INFO will suffice for a completed device
    
    
    def __init__(self, log, config_path='UPicoWSensorNode.json'):
        super().__init__(log, config_path)
        if self.config:
            self.MQTT_TOPIC_temperature = self.config.get('MQTT_TOPIC_temperature', '')
            self.MQTT_TOPIC_humidity = self.config.get('MQTT_TOPIC_humidity', '')
            self.MQTT_TOPIC_airPressure = self.config.get('MQTT_TOPIC_airPressure', '')
            self.log.log_message(f"{self.__class__.__name__} Config values applied", LogLevel.INFO)
        else:
            self.log.log_message(f"{self.__class__.__name__} Failed to load config file.", LogLevel.ERROR)
            
        self.log.log_message(f"{self.__class__.__name__} initialized.", LogLevel.DEBUG)
        
        from PiicoDev_BME280 import PiicoDev_BME280
        self.sensor = PiicoDev_BME280() # instantiate the sensor

#     def subclass_method(self):
#         self.log.log_message("INFO: "+ self.__class__.__name__ +" method called")


# default method values
#     def main(self):
#         # Call the main method of the ParentClass
#         super().main()exception in myNode ({})
#         self.log.log_message("INFO: Main method of "+ self.__class__.__name__ +" called")
#import time
#     def connect_broker(self):
#         self.log.log_message("INFO: connect_broker method of "+ self.__class__.__name__ +" called")
#         return None
#     
#     def initialize_broker(self):
#         self.log.log_message("INFO: initialize_broker method of "+ self.__class__.__name__ +" called")
#         return None    
# 
#     def disconnect_broker(self):
#         self.log.log_message("INFO: disconnect_broker method of "+ self.__class__.__name__ +" called")
#         return None
#     
#     def initialize_Sensors(self):
#         self.log.log_message("INFO: initialize_Sensors method of "+ self.__class__.__name__ +" called")
#         return None
#     
#     def read_sensor_data(self):
#         self.log.log_message("INFO: read_sensor_data method of "+ self.__class__.__name__ +" called")
#         return None
#     
#     def post_sensor_data(self):
#         self.log.log_message("INFO: post_sensor_data method of "+ self.__class__.__name__ +" called")
#         return None        


    def post_sensor_data(self):
        try:
            self.log_message("post_sensor_data", LogLevel.INFO) 
            
            self.log_message(f"{self.__class__.__name__}.post_sensor_data() {self.sensor_data['tempC']} to >{self.MQTT_TOPIC_temperature}", LogLevel.DEBUG)
            self.mqtt_client.publish(self.MQTT_TOPIC_temperature, f"{self.sensor_data['tempC']}")

            self.log_message(f"{self.__class__.__name__}.post_sensor_data() {self.sensor_data['pres_hPa']} to >{self.MQTT_TOPIC_airPressure}", LogLevel.DEBUG)
            self.mqtt_client.publish(self.MQTT_TOPIC_airPressure, f"{int(self.sensor_data['pres_hPa'])}")

            self.log_message(f"{self.__class__.__name__}.post_sensor_data() {self.sensor_data['humRH']} to >{self.MQTT_TOPIC_humidity}", LogLevel.DEBUG)
            self.mqtt_client.publish(self.MQTT_TOPIC_humidity, f"{int(self.sensor_data['humRH'])}")
            
            if self.LOG_SENSOR_DATA == "True":
                self.write_to_json(self.LOG_SENSOR_DATA_FILE, self.sensor_data)
            
        except Exception as e:
            self.log.log_message(f"{self.__class__.__name__}.post_sensor_data() {str(e)}", LogLevel.ERROR)
        return None

    def read_sensor_data(self):
        try:
            self.log_message("read_sensor_data ", LogLevel.DEBUG)
            # obtain sensor data
            self.sensor_data["tempC"], self.sensor_data["presPa"], self.sensor_data["humRH"] = self.sensor.values() # read all data from the sensor
            self.sensor_data["pres_hPa"]= self.sensor_data["presPa"] / 100 # convert air pressurr Pascals -> hPa (or mbar, if you prefer)
            self.log_message(f"{self.sensor_data['tempC']} °C  {self.sensor_data['pres_hPa']} hPa {self.sensor_data['humRH']} %RH", LogLevel.INFO)
        except Exception as e:
            self.log_message(f"ERROR: {self.__class__.__name__}.read_sensor_data() {str(e)}", LogLevel.ERROR)
        return None


log = URollingAppenderLog("AtmophericSensorNode.log", max_file_size_bytes=64720, max_backups=10, print_messages=True, log_level=AtmophericSensorNode.STATIC_NODE_LOG_LEVEL)

# Instantiate a SensorNode subclassed from UPicoWSensorNode and call its main method
if __name__ == "__main__":
    myNode = AtmophericSensorNode(log=log, config_path="config.json")
    
    while True:
        try:
            print("CONSOLE: starting myNode")
            log.log_message("main.py starting myNode", LogLevel.INFO)
            myNode.main()
        except Exception as e:
            print(f"CONSOLE: exception in myNode ({e})")
            log.log_message(f"main.py {str(e)}", LogLevel.ERROR)
            
        print(f"CONSOLE: retry in {myNode.STATIC_NODE_RESTART_DELAY}.")
        log.log_message(f"main.py retry in {myNode.STATIC_NODE_RESTART_DELAY} seconds.", LogLevel.INFO)
        time.sleep(myNode.STATIC_NODE_RESTART_DELAY)
#
