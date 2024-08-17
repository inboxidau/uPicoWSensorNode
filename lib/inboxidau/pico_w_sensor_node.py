from lib.inboxidau.rolling_appender_log import LogLevel  # type: ignore
import ujson  # type: ignore # used to load config data
import ubinascii  # type: ignore # used to generate a GUID
import machine  # type: ignore
import network  # type: ignore
import time  # type: ignore
from umqtt.robust import MQTTClient  # type: ignore
import ntptime  # type: ignore
import utime  # type: ignore

current_time_utc = ""
iso_date = ""

# setting this pin High will remove power, and wait for
# the next interval for Makerverse Nano Power Timer HAT
POWERDOWN = machine.Pin(22, machine.Pin.OUT)


class UPicoWSensorNode:

    # Used to designate the log level required, normally LogLevel.INFO will
    # suffice for a completed device
    STATIC_NODE_LOG_LEVEL = LogLevel.DEBUG

    # Used to delay restarting main() on an unhandled exception
    STATIC_NODE_RESTART_DELAY = 60

    # Used to designate the delay in seconds between sensor reading
    STATIC_NODE_SENSE_REPEAT_DELAY = 300

    # Used to determine how many time we retry to establish wi-fi connections.
    STATIC_WIFI_MAX_RETRIES = 3

    STATIC_WIFI_RETRY_DELAY = 1  # seconds

    def log_message(self, message, log_level=LogLevel.INFO):
        self.log.log_message(message, log_level, self.get_network_time())

    def set_network_time(self):
        try:
            ntptime.settime()  # Update the system time using NTP
            current_time_utc = utime.localtime()

            hours = current_time_utc[3]
            minutes = current_time_utc[4]
            seconds = current_time_utc[5]
            message = f"CONSOLE: SET current time utc: {hours:02d}:{minutes:02d}:{seconds:02d}"  # noqa: E501

            self.log_message(message, LogLevel.INFO)
        except Exception as e:
            exception_details = repr(e)
            self.log_message(f"{self.__class__.__name__}.set_network_time: {exception_details} ")  # noqa: E501

    def get_network_time(self, log_level=LogLevel.INFO):  # noqa: E501 getting the time usually needs to be silent
        iso_date = ""
        try:
            # Print the current time
            current_time_utc = utime.localtime()
            if log_level == LogLevel.DEBUG:
                message = f"CONSOLE: SET current time utc: {current_time_utc[3]:02d}:{current_time_utc[4]:02d}:{current_time_utc[5]:02d}"  # noqa: E501

                self.log_message(message, LogLevel.INFO)
            # Format the current time into ISO date format
            iso_date = (
                "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z".format(
                    current_time_utc[0],  # Year
                    current_time_utc[1],  # Month
                    current_time_utc[2],  # Day
                    current_time_utc[3],  # Hour
                    current_time_utc[4],  # Minute
                    current_time_utc[5]   # Second
                )
            )
            if log_level == LogLevel.DEBUG:
                print(f"CONSOLE: Get current time (ISO format): {iso_date}")
        except Exception as e:
            exception_details = repr(e)
            print(f"{self.__class__.__name__}.get_network_time:0001 {exception_details} ",  # noqa: E501
                  LogLevel.ERROR)

        return iso_date

    # Function to write data to a JSON file
    def write_to_json(self, file_path, data):
        try:
            self.log_message(f"opening {file_path} ", LogLevel.DEBUG)
            with open(file_path, 'w') as file:
                ujson.dump(data, file)
            self.log_message(f"Data successfully written to {file_path}",
                             LogLevel.DEBUG)
        except Exception as e:
            exception_details = repr(e)
            self.log_message(f"{self.__class__.__name__}.write_to_json: {exception_details} ",  # noqa: E501
                             LogLevel.DEBUG)

    def connect_broker(self):
        self.log_message(f"{self.__class__.__name__}.connect_broker() called",
                         LogLevel.DEBUG)
        self.log_message(f"Connecting to MQTT:{self.MQTT_BROKER}:{self.MQTT_PORT}",  # noqa: E501
                         LogLevel.DEBUG)
        self.mqtt_client.connect()
        self.log_message(f"MQTT:{self.MQTT_BROKER}:{self.MQTT_PORT} Connected.",  # noqa: E501
                         LogLevel.DEBUG)
        return None

    def initialize_broker(self):
        self.log_message(f"{self.__class__.__name__}.initialize_broker() called ",  # noqa: E501
                         LogLevel.DEBUG)
#         # SSL Context
#         ssl_params = {"ca_certs": self.MQTT_CA_CERTS}
        self.mqtt_client = MQTTClient(self.guid, self.MQTT_BROKER,
                                      port=self.MQTT_PORT,
                                      user=self.MQTT_USERNAME,
                                      password=self.MQTT_PASSWORD,
                                      ssl=True)

        # use device guid as MQTT Client ID
        self.log_message(f"Broker configured MQTTClient {self.guid}",
                         LogLevel.INFO)
        return None

    def disconnect_broker(self):
        try:
            self.mqtt_client.disconnect()
        except Exception as e:
            error_message = f"{self.__class__.__name__}.disconnect_broker() Error during disconnect_broker: {e}"  # noqa: E501
            print(error_message)
            raise RuntimeError(error_message, LogLevel.ERROR)

        return None

    def initialize_sensors(self):
        return None

    def read_sensor_data(self):
        return None

    def post_sensor_data(self):
        return None

    def generate_guid(self):
        # Generate a unique ID using the MAC address of the device
        mac = ubinascii.hexlify(machine.unique_id()).decode('utf-8')
        return mac

    def load_config(self, file_path):
        # load the config from the json fie into a config_data array
        try:
            with open(file_path, 'r') as file:
                config_data = ujson.load(file)
            self.log_message(f"{self.__class__.__name__} config loaded",
                             LogLevel.INFO)
            return config_data
        except Exception as e:
            exception_details = repr(e)
            self.log_message(
                f"{self.__class__.__name__}.load_config() Unable to load config {file_path} {exception_details}",  # noqa: E501
                LogLevel.ERROR
            )

            raise ValueError(exception_details)
            return None

    def force_boolean(self, json_value, key="Unspecified"):
        # Check if the JSON value is a string
        if isinstance(json_value, str):
            self.log_message(
                f"String value detected and replaced with a boolean for key= {key}",  # noqa: E501
                LogLevel.ERROR
            )

            if json_value.lower() == "true":
                return True
            else:
                return False
        else:
            return json_value

    def __init__(self, log, config_path='UPicoWSensorNode.json'):
        self.mqtt_client = None
        self.log = log                                       # noqa: E501 Assign the log variable passed from main.py
        self.config_path = config_path                       # noqa: E501 Assign the path to the config file
        self.config = self.load_config(config_path)
        self.guid = self.generate_guid()                     # noqa: E501 Assign a device ID for reference
        self.sensor_data = {}                                # noqa: E501 Assign an empty dictionary for sensor data
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
            # flake8 max line warning avoidance using hat_value
            hat_value = self.config.get('MAKERVERSE_NANO_POWER_TIMER_HAT',
                                        "False")
            self.MAKERVERSE_NANO_POWER_TIMER_HAT = self.force_boolean(hat_value, 'MAKERVERSE_NANO_POWER_TIMER_HAT')  # noqa: E501
            self.LOG_SENSOR_DATA = self.force_boolean(self.config.get('LOG_SENSOR_DATA', 'False'), 'LOG_SENSOR_DATA')  # noqa: E501
            self.LOG_SENSOR_DATA_FILE = self.config.get('LOG_SENSOR_DATA_FILE', 'main.dat')  # noqa: E501
            self.log_message(f"SENSOR LOG {self.LOG_SENSOR_DATA} {self.LOG_SENSOR_DATA_FILE}", LogLevel.DEBUG)  # noqa: E501

            self.log_message("UPicoWSensorNode Config values applied",
                             LogLevel.DEBUG)
        else:
            self.log_message("UPicoWSensorNode Failed to load config file.",
                             LogLevel.ERROR)

        self.log_message(f"UPicoWSensorNode initialized device with guid {self.guid}", LogLevel.DEBUG)  # noqa: E501

    def cycle_makerverse_nano_hat(self):
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

    def execute_sensor_reading(self):
        try:
            self.read_sensor_data()
            self.post_sensor_data()
        finally:
            self.disconnect_broker()
            self.log_message("MQTT: Disconnected.", LogLevel.DEBUG)

    def initialize_wifi(self):
        self.wifi = network.WLAN(network.STA_IF)
        self.wifi.disconnect()
        self.wifi.active(True)
        self.wifi.connect(self.WIFI_SSID, self.WIFI_PASSWORD)

    def wait_for_wifi_connection(self):
        retries_remaining = self.STATIC_WIFI_MAX_RETRIES
        for _ in range(self.STATIC_WIFI_MAX_RETRIES):
            if self.wifi.isconnected():
                break
            self.log_message(
                f'Waiting for re-connection to {self.WIFI_SSID}. Retries left: {retries_remaining}',  # noqa: E501
                LogLevel.DEBUG
            )

            time.sleep(self.STATIC_WIFI_RETRY_DELAY)
            retries_remaining -= 1
        else:
            self.log_message(f'{self.__class__.__name__}.connect_to_wifi() {self.WIFI_SSID} network connection failed', LogLevel.ERROR)  # noqa: E501

            raise RuntimeError('network connection failed.', LogLevel.ERROR)

    def connect_to_wifi(self):
        # Check if already connected
        if self.wifi.status() != 3:
            self.log_message(f"Connecting to {self.WIFI_SSID}...",
                             LogLevel.INFO)
            self.initialize_wifi()
            self.wait_for_wifi_connection()
            self.set_network_time()

    def main(self):
        self.wifi = network.WLAN(network.STA_IF)
        self.connect_to_wifi()
        self.initialize_broker()

        # Main Sensor Node execution
        while True:
            try:
                self.initialize_sensors()  # noqa: E501 ensure sensors are ready for reading
                self.connect_broker()      # noqa: E501 ensure that the broker client is ready for posting
                while True:
                    # Connect to Wi-Fi if not connected
                    self.connect_to_wifi()

                    self.execute_sensor_reading()
                    self.cycle_makerverse_nano_hat()

                    self.log_message(f"Sleeping {self.STATIC_NODE_SENSE_REPEAT_DELAY} seconds.",  # noqa: E501
                                     LogLevel.INFO)
                    time.sleep(self.STATIC_NODE_SENSE_REPEAT_DELAY)

            except Exception as e:
                # sys.print_exception(e)  # Print basic exception information
                exception_details = f"{self.__class__.__name__}.main() {repr(e)}"  # noqa: E501
                self.log_message(exception_details, LogLevel.ERROR)

            self.log_message(f"{self.__class__.__name__}.Main() Sleeping on exception recovery", LogLevel.INFO)  # noqa: E501
            time.sleep(self.STATIC_NODE_SENSE_REPEAT_DELAY)
        #         self.log_message("Main method of UPicoWSensorNode called")
