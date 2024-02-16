from rolling_appender_log import URollingAppenderLog, LogLevel
from pico_w_sensor_node import UPicoWSensorNode

class DistanceSensorNode(UPicoWSensorNode):
    def __init__(self, log, config_path='UPicoWSensorNode.json'):
        super().__init__(log, config_path)
        if self.config:
            self.MQTT_TOPIC_distance = self.config.get('MQTT_TOPIC_distance', '')
            self.MQTT_TOPIC_occupancy = self.config.get('MQTT_TOPIC_occupancy', '')
            self.OCCUPANCY_DISTANCE = self.config.get('OCCUPANCY_DISTANCE', '')
            self.log.log_message(self.__class__.__name__ +" Config values applied", LogLevel.INFO)           
        else:
            self.log.log_message(self.__class__.__name__ +" Failed to load config file.",LogLevel.ERROR)
            
        self.log.log_message(self.__class__.__name__ +" initialized", LogLevel.INFO)
        
        from PiicoDev_VL53L1X import PiicoDev_VL53L1X
        self.distance_sensor = PiicoDev_VL53L1X() # initialise the sensor
        

#     def subclass_method(self):
#         self.log.log_message("INFO: "+ self.__class__.__name__ +" method called")


# default method values
#     def main(self):
#         # Call the main method of the ParentClass
#         super().main()
#         self.log.log_message("INFO: Main method of "+ self.__class__.__name__ +" called")
#
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
        self.log.log_message('post_sensor_data method from {}: {}'.format(self.__class__.__name__,self.sensor_data["distance"]) )  
        self.mqtt_client.publish(self.MQTT_TOPIC_distance, '{}'.format(self.sensor_data["distance"]))
        #self.mqtt_client.publish(self.MQTT_TOPIC_occupancy, '{}'.format(self.sensor_data["distance"] <= self.OCCUPANCY_DISTANCE))
        self.mqtt_client.publish(self.MQTT_TOPIC_occupancy, '{}'.format(int((self.sensor_data["distance"] <= self.OCCUPANCY_DISTANCE))))
        return None

    def read_sensor_data(self):
        self.log.log_message("read_sensor_data method of "+ self.__class__.__name__ +" called", LogLevel.DEBUG)
        self.sensor_data["distance"] = self.distance_sensor.read() # read the distance in millimetres
        self.log.log_message(str( self.sensor_data["distance"]) + " mm", LogLevel.DEBUG)
        return None


log = URollingAppenderLog("main.log", max_file_size_bytes=1024, max_backups=1, print_messages=True, log_level=LogLevel.INFO)

# Instantiate a SensorNode subclassed from UPicoWSensorNode and call its main method
if __name__ == "__main__":
    myNode = DistanceSensorNode(log=log, config_path="config.json")
    myNode.main()