from rolling_appender_log import URollingAppenderLog, LogLevel
import ujson # used to load config data
import ubinascii # used to generate a GUID
import machine
import network
import time
from umqtt.robust import MQTTClient

POWERDOWN = machine.Pin(22, machine.Pin.OUT) # setting this pin High will remove power, and wait for the next interval for Makerverse Nano Power Timer HAT

class UPicoWSensorNode:
    
    # Function to write data to a JSON file
    def write_to_json(self, file_path, data):
        try:
            self.log.log_message("opening {} ".format(file_path), LogLevel.DEBUG)
            with open(file_path, 'w') as file:
                ujson.dump(data, file)
            self.log.log_message("Data successfully written to {}".format(file_path), LogLevel.DEBUG)
        except Exception as e:
            exception_details = repr(e)
            self.log.log_message("write_to_json: {} ".format(exception_details), LogLevel.DEBUG)
    
    def connect_broker(self):
        self.log.log_message("{}.connect_broker() called".format( self.__class__.__name__ ), LogLevel.DEBUG)
        self.log.log_message("Connecting to MQTT:{}:{}".format(self.MQTT_BROKER,self.MQTT_PORT), LogLevel.DEBUG)
        self.mqtt_client.connect()
        self.log.log_message("MQTT:{}:{} Connected.".format(self.MQTT_BROKER,self.MQTT_PORT), LogLevel.DEBUG)
        return None
    
    def initialize_broker(self):
        self.log.log_message("{}.initialize_broker() called ".format(self.__class__.__name__ ), LogLevel.DEBUG)        
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
            self.log.log_message("re-connecting to {}...".format(WIFI_SSID), LogLevel.INFO)
            self.wifi.connect(WIFI_SSID, WIFI_PASSWORD)
            
            # Wait for connection
            while not self.wifi.isconnected():
                pass
            
            self.log.log_message("Connected to {}.".format(WIFI_SSID), LogLevel.INFO)
        
        
    def generate_guid(self):
        # Generate a unique ID using the MAC address of the device
        mac = ubinascii.hexlify(machine.unique_id()).decode('utf-8')
        return mac
    
    def load_config(self,file_path):
        # load the config from the json fie into a config_data array
        try:
            with open(file_path, 'r') as file:
                config_data = ujson.load(file)
            self.log.log_message("{} config loaded".format(file_path))    
            return config_data
        except Exception as e:
            exception_details = repr(e)
            self.log.log_message("Unable to load config {} {}".format(file_path,exception_details), LogLevel.ERROR)
            raise ValueError(exception_details)
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
            self.MAKERVERSE_NANO_POWER_TIMER_HAT = self.config.get('MAKERVERSE_NANO_POWER_TIMER_HAT', False)
            self.LOG_SENSOR_DATA = self.config.get('LOG_SENSOR_DATA', 'False')
            self.LOG_SENSOR_DATA_FILE = self.config.get('LOG_SENSOR_DATA_FILE', 'aaaaaaaaaaaaaaaaaaaa.dat')
            self.log.log_message("SENSOR LOG {} {}".format(self.LOG_SENSOR_DATA,self.LOG_SENSOR_DATA_FILE), LogLevel.DEBUG)
            
            self.log.log_message("UPicoWSensorNode Config values applied", LogLevel.DEBUG)   
        else:
            self.log.log_message("UPicoWSensorNode Failed to load config file.", LogLevel.ERROR)

        self.log.log_message("UPicoWSensorNode initialized device with guid {}".format(self.guid), LogLevel.DEBUG)

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
            self.log.log_message('waiting for connection to {}'.format(self.WIFI_SSID), LogLevel.DEBUG)
            time.sleep(1)

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
                          self.log.log_message("MQTT: Disconnected.", LogLevel.DEBUG)
                          
                    if self.MAKERVERSE_NANO_POWER_TIMER_HAT == "True":
                        self.log.log_message("Power down HAT.", LogLevel.INFO)
                        POWERDOWN.on()
                        
                    self.log.log_message("Sleeping", LogLevel.DEBUG)
                    time.sleep(15)
                    
            except Exception as e:
                #sys.print_exception(e)  # Print basic exception information
                exception_details = repr(e)
                self.log.log_message(exception_details, LogLevel.ERROR)

            self.log.log_message("Sleeping", LogLevel.DEBUG)
            time.sleep(15)         
        #         self.log.log_message("Main method of UPicoWSensorNode called")
