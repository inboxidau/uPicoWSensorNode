from lib.inboxidau.pico_w_sensor_node import UPicoWSensorNode
from lib.inboxidau.rolling_appender_log import LogLevel


class AtmosphericSensorNode(UPicoWSensorNode):

    # Used to delay restarting main() on an unhandled exception STATIC_NODE_RESTART_DELAY = 60

    # Used to designate the log level required, normally LogLevel.INFO will suffice for a completed device
    STATIC_NODE_LOG_LEVEL = LogLevel.INFO

    POST_SENSOR_DATA_FORMAT = "{}.post_sensor_data() {} to >{}"

    def __init__(self, log, config_path='AtmosphericSensorNode.json'):
        super().__init__(log, config_path)
        if self.config:
            self.MQTT_TOPIC_temperature = self.config.get('MQTT_TOPIC_temperature', '')
            self.MQTT_TOPIC_humidity = self.config.get('MQTT_TOPIC_humidity', '')
            self.MQTT_TOPIC_airPressure = self.config.get('MQTT_TOPIC_airPressure', '')
            self.log.log_message(f"{self.__class__.__name__} Config values applied", LogLevel.INFO)
        else:
            self.log.log_message(f"{self.__class__.__name__} Failed to load config file.", LogLevel.ERROR)

        self.log.log_message(f"{self.__class__.__name__} initialized.", LogLevel.DEBUG)

        from lib.PiicoDev_BME280 import PiicoDev_BME280
        self.sensor = PiicoDev_BME280()  # instantiate the sensor

    def post_sensor_data(self):
        try:
            self.log_message("post_sensor_data", LogLevel.INFO)

            log_message = self.POST_SENSOR_DATA_FORMAT.format(
                self.__class__.__name__,
                self.sensor_data['tempC'],
                self.MQTT_TOPIC_temperature
             )
            self.log_message(log_message, LogLevel.DEBUG)
            self.mqtt_client.publish(self.MQTT_TOPIC_temperature, f"{self.sensor_data['tempC']}")

            log_message = self.POST_SENSOR_DATA_FORMAT.format(
                self.__class__.__name__,
                self.sensor_data['pres_hPa'],
                self.MQTT_TOPIC_airPressure
             )
            self.log_message(log_message, LogLevel.DEBUG)
            self.mqtt_client.publish(self.MQTT_TOPIC_airPressure, f"{int(self.sensor_data['pres_hPa'])}")

            log_message = self.POST_SENSOR_DATA_FORMAT.format(
                self.__class__.__name__,
                self.sensor_data['humRH'],
                self.MQTT_TOPIC_humidity
             )
            self.log_message(log_message, LogLevel.DEBUG)
            self.mqtt_client.publish(self.MQTT_TOPIC_humidity, f"{int(self.sensor_data['humRH'])}")

            if self.LOG_SENSOR_DATA == 1:
                self.write_to_json(self.LOG_SENSOR_DATA_FILE, self.sensor_data)

        except Exception as e:
            self.log.log_message(f"{self.__class__.__name__}.post_sensor_data() {str(e)}", LogLevel.ERROR)
        return None

    def read_sensor_data(self):
        try:
            self.log_message("read_sensor_data ", LogLevel.DEBUG)
            # read all data from the sensor
            self.sensor_data["tempC"], self.sensor_data["presPa"], self.sensor_data["humRH"] = self.sensor.values()

            # convert air pressure Pascals -> hPa (or mbar, if you prefer)
            self.sensor_data["pres_hPa"] = self.sensor_data["presPa"] / 100

            self.log_message(
                f"{self.sensor_data['tempC']} °C  {self.sensor_data['pres_hPa']} hPa {self.sensor_data['humRH']} %RH",
                LogLevel.INFO)
        except Exception as e:
            self.log_message(f"ERROR: {self.__class__.__name__}.read_sensor_data() {str(e)}", LogLevel.ERROR)
        return None
