from rolling_appender_log import URollingAppenderLog, LogLevel
import ujson # used to load config data
import ubinascii # used to generate a GUID
import machine
import network
import time
from umqtt.robust import MQTTClient
import ntptime
import utime

current_time_utc = ""
iso_date = ""

POWERDOWN = machine.Pin(22, machine.Pin.OUT) # setting this pin High will remove power, and wait for the next interval for Makerverse Nano Power Timer HAT

class UPicoWSensorNode:
    
    STATIC_NODE_RESTART_DELAY = 60               # Used to delay restraing main() on an unhandled exception
    STATIC_NODE_LOG_LEVEL = LogLevel.DEBUG        # Used to designate the log level required, normally LogLevel.INFO will suffice for a completed device
    STATIC_NODE_SENSE_REPEAT_DELAY = 300         # Used to designate the delay in seconds between sensor reading

    
    def log_message(self, message, log_level=LogLevel.INFO):
        self.log.log_message(message,log_level, self.get_network_time())
        
    def set_network_time(self):
        try:
            ntptime.settime() # Update the system time using NTP
            current_time_utc = utime.localtime()
            self.log_message(f"CONSOLE: SET current time utc: {current_time_utc[3]:02d}:{current_time_utc[4]:02d}:{current_time_utc[5]:02d}", LogLevel.INFO)
        except Exception as e:
            exception_details = repr(e)
            self.log_message(f"{self.__class__.__name__}.set_network_time: {exception_details} ")

    def get_network_time(self, log_level=LogLevel.INFO): #getting the time usually needs to be silent
        iso_date = ""
        try:
            # Print the current time
            current_time_utc = utime.localtime()
            if log_level==LogLevel.DEBUG:
                print(f"CONSOLE: Current time utc: {current_time_utc[3]:02d}:{current_time_utc[4]:02d}:{current_time_utc[5]:02d}")
            # Format the current time into ISO date format
            iso_date = "%04d-%02d-%02dT%02d:%02d:%02dZ" % (current_time_utc[0], current_time_utc[1], current_time_utc[2], 
                                                    current_time_utc[3], current_time_utc[4], current_time_utc[5])
            if log_level == LogLevel.DEBUG:
                print(f"CONSOLE: Get current time (ISO format): {iso_date}")
        except Exception as e:
            exception_details = repr(e)
            print(f"{self.__class__.__name__}.get_network_time:0001 {exception_details} ", LogLevel.ERROR)
        finally:
            return iso_date
        
    # Function to write data to a JSON file
    def write_to_json(self, file_path, data):
        try:
            self.log_message(f"opening {file_path} ", LogLevel.DEBUG)
            with open(file_path, 'w') as file:
                ujson.dump(data, file)
            self.log_message(f"Data successfully written to {file_path}", LogLevel.DEBUG)
        except Exception as e:
            exception_details = repr(e)
            self.log_message(f"{self.__class__.__name__}.write_to_json: {exception_details} ", LogLevel.DEBUG)
    
    def connect_broker(self):
        self.log_message(f"{self.__class__.__name__}.connect_broker() called", LogLevel.DEBUG)
        self.log_message(f"Connecting to MQTT:{self.MQTT_BROKER}:{self.MQTT_PORT}", LogLevel.DEBUG)
        self.mqtt_client.connect()
        self.log_message(f"MQTT:{self.MQTT_BROKER}:{self.MQTT_PORT} Connected.", LogLevel.DEBUG)
        return None
    
    def initialize_broker(self):
        self.log_message(f"{self.__class__.__name__}.initialize_broker() called ", LogLevel.DEBUG)        
#         # SSL Context
#         ssl_params = {"ca_certs": self.MQTT_CA_CERTS}
        self.mqtt_client = MQTTClient(self.guid, self.MQTT_BROKER, port=self.MQTT_PORT,user=self.MQTT_USERNAME, password=self.MQTT_PASSWORD,ssl=True)
        self.log_message(f"Broker configured MQTTClient {self.guid}", LogLevel.INFO) # use device guid as MQTT Client ID      
        return None

    def disconnect_broker(self):
        try:
            self.mqtt_client.disconnect()
        except Exception as e:
            error_message = f"{self.__class__.__name__}.disconnect_broker() Error during disconnect_broker: {e}"
            print(error_message)
            raise RuntimeError(error_message, LogLevel.ERROR)
        
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
            self.log_message(f"re-connecting to {self.WIFI_SSID}...", LogLevel.INFO)
            self.wifi.connect(WIFI_SSID, WIFI_PASSWORD)
            
            # Wait for connection
            self.max_wait = 10
            while self.max_wait > 0:
                if self.wifi.isconnected():
                    break
                raise RuntimeError('network connection failed.', LogLevel.ERROR)
                self.max_wait -= 1
                self.log_message(f'waiting for re-connection to {self.WIFI_SSID}', LogLevel.DEBUG)
                sleep(1)

            if self.wifi.status() != 3:
                self.log_message(f'{self.__class__.__name__}.connect_to_wifi() {self.WIFI_SSID} network connection failed', LogLevel.ERROR)
                raise RuntimeError('network connection failed.', LogLevel.ERROR)
            else:
                self.log_message(f"Reconnected to {self.WIFI_SSID} channel {self.wifi.config('channel')} with address {self.wifi.ifconfig()[0]}", LogLevel.INFO)
            self.set_network_time()
            
    def generate_guid(self):
        # Generate a unique ID using the MAC address of the device
        mac = ubinascii.hexlify(machine.unique_id()).decode('utf-8')
        return mac
    
    def load_config(self,file_path):
        # load the config from the json fie into a config_data array
        try:
            with open(file_path, 'r') as file:
                config_data = ujson.load(file)
            self.log_message(f"{self.__class__.__name__} config loaded", LogLevel.INFO)
            return config_data
        except Exception as e:
            exception_details = repr(e)
            self.log_message(f"{self.__class__.__name__}.load_config() Unable to load config {file_path} {exception_details}", LogLevel.ERROR)
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
            self.LOG_SENSOR_DATA_FILE = self.config.get('LOG_SENSOR_DATA_FILE', 'main.dat')
            self.log_message(f"SENSOR LOG {self.LOG_SENSOR_DATA} {self.LOG_SENSOR_DATA_FILE}", LogLevel.DEBUG)
            
            self.log_message("UPicoWSensorNode Config values applied", LogLevel.DEBUG)   
        else:
            self.log_message("UPicoWSensorNode Failed to load config file.", LogLevel.ERROR)

        self.log_message(f"UPicoWSensorNode initialized device with guid {self.guid}", LogLevel.DEBUG)
        
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
            self.log_message(f"waiting {self.max_wait} for connection to {self.WIFI_SSID}", LogLevel.DEBUG)
            time.sleep(1)

        if self.wifi.status() != 3:
            self.log_message(f'{self.__class__.__name__} network connection failed Status {self.WIFI_SSID}', LogLevel.ERROR)
            raise RuntimeError(f'network connection failed. Status {self.WIFI_SSID}', LogLevel.ERROR)
        else:
            self.log_message(f"Connected to {self.WIFI_SSID} channel {self.wifi.config('channel')} with address {self.wifi.ifconfig()[0]}")
            self.set_network_time()
        
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
                          self.log_message("MQTT: Disconnected.", LogLevel.DEBUG)
                          
                    if self.MAKERVERSE_NANO_POWER_TIMER_HAT == "True":
                        self.log_message("Power down HAT.", LogLevel.INFO)
                        POWERDOWN.on()
                        count = 0
                        max_count = 30
                        while True:
                            if count >= max_count:
                                break  # Exit the loop after reaching maximum count
                            self.log_message(f"count {count} sheep.", LogLevel.DEBUG)
                            count += 1
                            time.sleep(1)  # Sleep for 1 second between each output                        
                        
                    self.log_message(f"Sleeping {UPicoWSensorNode.STATIC_NODE_SENSE_REPEAT_DELAY} seconds.", LogLevel.INFO)
                    time.sleep(UPicoWSensorNode.STATIC_NODE_SENSE_REPEAT_DELAY)
                    
            except Exception as e:
                #sys.print_exception(e)  # Print basic exception information
                exception_details = f"{self.__class__.__name__}.main() {repr(e)}"
                self.log_message(exception_details, LogLevel.ERROR)

            self.log_message(f"{self.__class__.__name__}.Main() Sleeping on exception recovery", LogLevel.INFO)
            time.sleep(UPicoWSensorNode.STATIC_NODE_SENSE_REPEAT_DELAY)         
        #         self.log_message("Main method of UPicoWSensorNode called")

