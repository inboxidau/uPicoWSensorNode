from rolling_appender_log import URollingAppenderLog, LogLevel
from pico_w_sensor_node import UPicoWSensorNode
import time

class AtmophericSensorNode(UPicoWSensorNode):
    
    #STATIC_NODE_RESTART_DELAY = 60               # Used to delay restraing main() on an unhandled exception
    #STATIC_NODE_LOG_LEVEL = LogLevel.DEBUG       # Used to designate the log level required, normally LogLevel.INFO will suffice for a completed device
    
    
    def __init__(self, log, config_path='UPicoWSensorNode.json'):
        super().__init__(log, config_path)
        if self.config:
            self.MQTT_TOPIC_temperature = self.config.get('MQTT_TOPIC_temperature', '')
            self.MQTT_TOPIC_humidity = self.config.get('MQTT_TOPIC_humidity', '')
            self.MQTT_TOPIC_airPressure = self.config.get('MQTT_TOPIC_airPressure', '')
            self.log.log_message("{} Config values applied".format(self.__class__.__name__), LogLevel.INFO)           
        else:
            self.log.log_message("{} Failed to load config file.".format(self.__class__.__name__ ),LogLevel.ERROR)
            
        self.log.log_message("{} initialized.".format(self.__class__.__name__ ), LogLevel.DEBUG)
        
        from PiicoDev_BME280 import PiicoDev_BME280
        self.sensor = PiicoDev_BME280() # initialise the sensor
        

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
            self.log.log_message("post_sensor_data", LogLevel.INFO) 
            self.log.log_message('{}.post_sensor_data() {} to >{}'.format(self.__class__.__name__, self.sensor_data["tempC"],self.MQTT_TOPIC_temperature), LogLevel.DEBUG)  
            self.mqtt_client.publish(self.MQTT_TOPIC_temperature, '{}'.format(self.sensor_data["tempC"]))

            self.log.log_message('{}.post_sensor_data() {} to >{}'.format(self.__class__.__name__, self.sensor_data["pres_hPa"],self.MQTT_TOPIC_airPressure), LogLevel.DEBUG)  
            self.mqtt_client.publish(self.MQTT_TOPIC_airPressure, '{}'.format(int(self.sensor_data["pres_hPa"])))

            self.log.log_message('{}.post_sensor_data() {} to >{}'.format(self.__class__.__name__, self.sensor_data["humRH"],self.MQTT_TOPIC_humidity), LogLevel.DEBUG)  
            self.mqtt_client.publish(self.MQTT_TOPIC_humidity, '{}'.format(int(self.sensor_data["humRH"])))
            
            if self.LOG_SENSOR_DATA == "True":
                self.write_to_json(self.LOG_SENSOR_DATA_FILE, self.sensor_data)
            
        except Exception as e:
            self.log.log_message("{}.post_sensor_data() {}".format( self.__class__.__name__ , str(e)), LogLevel.ERROR)
        return None

    def read_sensor_data(self):
        try:
            self.log.log_message("read_sensor_data ", LogLevel.DEBUG)
            # obtain sensor data
            self.sensor_data["tempC"], self.sensor_data["presPa"], self.sensor_data["humRH"] = self.sensor.values() # read all data from the sensor
            self.sensor_data["pres_hPa"]= self.sensor_data["presPa"] / 100 # convert air pressurr Pascals -> hPa (or mbar, if you prefer)
            self.log.log_message("{} °C  {} hPa {} %RH".format(self.sensor_data["tempC"], self.sensor_data["pres_hPa"], self.sensor_data["humRH"]), LogLevel.INFO)                
        except Exception as e:
            self.log.log_message("ERROR: {}.read_sensor_data() {} ".format( self.__class__.__name__ , str(e)), LogLevel.ERROR)
        return None


log = URollingAppenderLog("AtmophericSensorNode.log", max_file_size_bytes=64720, max_backups=10, print_messages=True, log_level=AtmophericSensorNode.STATIC_NODE_LOG_LEVEL)

# Instantiate a SensorNode subclassed from UPicoWSensorNode and call its main method
if __name__ == "__main__":
    myNode = AtmophericSensorNode(log=log, config_path="config.json")
    
    while True:
        try:
            #print("CONSOLE: starting myNode")
            log.log_message("main.py starting myNode", LogLevel.INFO)
            myNode.main()
        except Exception as e:
#            print("CONSOLE: exception in myNode ({})".format(e))
            log.log_message("main.py {} ".format(str(e)), LogLevel.ERROR)
            
        #print("CONSOLE: retry in {}.".format(myNode.STATIC_NODE_RESTART_DELAY))
        log.log_message("main.py retry in {} seconds.".format(myNode.STATIC_NODE_RESTART_DELAY), LogLevel.INFO)
        time.sleep(myNode.STATIC_NODE_RESTART_DELAY)
#
