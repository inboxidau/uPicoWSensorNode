from rolling_appender_log import URollingAppenderLog, LogLevel
import ujson # used to load config data
import ubinascii # used to generate a GUID
import machine
import network
import time
from umqtt.robust import MQTTClient

class UPicoWSensorNode:
    
    def connect_broker(self):
        self.log.log_message("connect_broker method of "+ self.__class__.__name__ +" called", LogLevel.DEBUG)
        self.log.log_message("Connecting to MQTT:{}:{}".format(self.MQTT_BROKER,self.MQTT_PORT), LogLevel.DEBUG)
        self.mqtt_client.connect()
        self.log.log_message("Connected to MQTT:{}:{}".format(self.MQTT_BROKER,self.MQTT_PORT))
        return None
    
    def initialize_broker(self):
        self.log.log_message("Initialize_broker method of "+ self.__class__.__name__ +" called", LogLevel.DEBUG)        
#         # SSL Context
#         ssl_params = {"ca_certs": self.MQTT_CA_CERTS}
        self.mqtt_client = MQTTClient(self.guid, self.MQTT_BROKER, port=self.MQTT_PORT,user=self.MQTT_USERNAME, password=self.MQTT_PASSWORD,ssl=True)
        self.log.log_message("Broker configured MQTTClient {}".format(self.guid), LogLevel.INFO) # use device guid as MQTT Client ID      
        return None

    def disconnect_broker(self):
        self.mqtt_client.disconnect()
        return None
    
    def initialize_Sensors(self):
        return None
    
    def read_sensor_data(self):
        return None
    
    def post_sensor_data(self):
        return None
    
    def connect_to_wifi(self):
        # Check if already connected
        if self.wifi.status() != 3:
            self.log.log_message("re-connecting to Wi-Fi...")
            self.wifi.connect(WIFI_SSID, WIFI_PASSWORD)
            
            # Wait for connection
            while not self.wifi.isconnected():
                pass
            
            self.log.log_message("Connected to Wi-Fi")
        
        
    def generate_guid(self):
        # Generate a unique ID using the MAC address of the device
        mac = ubinascii.hexlify(machine.unique_id()).decode('utf-8')
        return mac
    
    def load_config(self,file_path):
        # load the config from the json fie into a config_data array
        try:
            with open(file_path, 'r') as file:
                config_data = ujson.load(file)
            self.log.log_message("Config file loaded")    
            return config_data
        except Exception as e:
            exception_details = repr(e)
            msg = "Unable to load config ("+file_path+")" + exception_details
            self.log.log_message(msg, LogLevel.ERROR)
            raise ValueError(msg)
            return None
    
    def __init__(self, log, config_path='UPicoWSensorNode.json'):
        self.mqtt_client = None
        self.log = log                                     # Assign the log variable passed from main.py
        self.config_path = config_path                     # Assign the path to the config file
        self.config = self.load_config(config_path)
        self.guid = self.generate_guid()                   # Assign a device ID for reference
        self.sensor_data = {}                              # Assign an empty dictionary for sensor data
        if self.config:
            # Global Wi-Fi credentials
            self.WIFI_SSID = self.config.get('WIFI_SSID', '')
            self.WIFI_PASSWORD = self.config.get('WIFI_PASSWORD', '')
            # MQTT Broker Details
            self.MQTT_BROKER = self.config.get('MQTT_BROKER', '')
            self.MQTT_PORT = self.config.get('MQTT_PORT', 0)
            self.MQTT_USERNAME = self.config.get('MQTT_USERNAME', '')
            self.MQTT_PASSWORD = self.config.get('MQTT_PASSWORD', 0)
            self.MQTT_CA_CERTS = self.config.get('MQTT_CA_CERTS', '')
            
            self.log.log_message("UPicoWSensorNode Config values applied", LogLevel.DEBUG)   
        else:
            self.log.log_message("UPicoWSensorNode Failed to load config file.", LogLevel.ERROR)

        self.log.log_message("UPicoWSensorNode initialized device with guid "+ self.guid, LogLevel.DEBUG)

    def main(self):
        #initialize wifi
        self.wifi = network.WLAN(network.STA_IF)
        self.wifi.disconnect()
        self.wifi.active(True)
        self.wifi.connect(self.WIFI_SSID, self.WIFI_PASSWORD)
        # Wait for connect or fail
        self.max_wait = 10
        while self.max_wait > 0:
            if self.wifi.status() < 0 or self.wifi.status() >= 3:
                break
            self.max_wait -= 1
            self.log.log_message('waiting for connection to '+self.WIFI_SSID, LogLevel.DEBUG)
            time.sleep(1)

        self.log.log_message('Initial connection complete')
        if self.wifi.status() != 3:
            raise RuntimeError('network connection failed.', LogLevel.ERROR)
        else:
            self.log.log_message("Connected to {} channel {} with address {}".format(self.WIFI_SSID,self.wifi.config('channel'), self.wifi.ifconfig()[0]))
        
        # prepare the broker connection
        self.initialize_broker()
        
        # Main Sensor Node execution
        while True:
            try:
                self.initialize_Sensors() # ensure sensors are ready for reading
                self.connect_broker()  #ensure that the broker client is ready for posting
                while True:
                    # Connect to Wi-Fi if not connected
                    self.connect_to_wifi()

                    try:
                          self.read_sensor_data()
                          self.post_sensor_data()
                    finally:
                          self.disconnect_broker()
                          self.log.log_message("Sleeping", LogLevel.DEBUG)
                          time.sleep(15)                           
                    
#                     logger.log_message ("Power Off")
#                     DONE.on() # Assert DONE signal; powers down Pico for Makerverse Nano Power Timer HAT
#                     logger.log_message("Power Off 2")
#                     Pin(22, Pin.OUT)

            except Exception as e:
                #sys.print_exception(e)  # Print basic exception information
                exception_details = repr(e)
                self.log.log_message(exception_details, LogLevel.ERROR)

            self.log.log_message("Sleeping", LogLevel.DEBUG)
            time.sleep(15)         
        #         self.log.log_message("Main method of UPicoWSensorNode called")
