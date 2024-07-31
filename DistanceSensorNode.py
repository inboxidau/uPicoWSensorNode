from lib.inboxidau.pico_w_sensor_node import UPicoWSensorNode
from lib.inboxidau.rolling_appender_log import LogLevel


class DistanceSensorNode(UPicoWSensorNode):

    # Used to delay restarting main() on an unhandled exception STATIC_NODE_RESTART_DELAY = 60

    # Used to designate the log level required, normally LogLevel.INFO will suffice for a completed device
    STATIC_NODE_LOG_LEVEL = LogLevel.INFO

    POST_SENSOR_DATA_FORMAT = "{}.post_sensor_data() {} to >{}"

    def __init__(self, log, config_path='UPicoWSensorNode.json'):
        super().__init__(log, config_path)
        if self.config:
            self.MQTT_TOPIC_distance = self.config.get('MQTT_TOPIC_distance', '')
            self.MQTT_TOPIC_occupancy = self.config.get('MQTT_TOPIC_occupancy', '')
            self.OCCUPANCY_DISTANCE = self.config.get('OCCUPANCY_DISTANCE', '')
            self.log.log_message("{} Config values applied".format(self.__class__.__name__), LogLevel.INFO)
        else:
            self.log.log_message("{} Failed to load config file.".format(self.__class__.__name__), LogLevel.ERROR)

        self.log.log_message("{} initialized.".format(self.__class__.__name__), LogLevel.DEBUG)

        from lib.PiicoDev_VL53L1X import PiicoDev_VL53L1X
        self.distance_sensor = PiicoDev_VL53L1X()  # initialise the sensor

    def post_sensor_data(self):
        try:
            self.log_message("post_sensor_data", LogLevel.INFO)

            log_message = self.POST_SENSOR_DATA_FORMAT.format(
                self.__class__.__name__,
                self.sensor_data["distance"],
                self.MQTT_TOPIC_temperature
             )
            self.log_message(log_message, LogLevel.DEBUG)
            self.mqtt_client.publish(self.MQTT_TOPIC_distance, f"{self.sensor_data['distance']}")

            log_message = self.POST_SENSOR_DATA_FORMAT.format(
                self.__class__.__name__,
                self.sensor_data["occupancy"],
                self.MQTT_TOPIC_temperature)

            self.log_message(log_message, LogLevel.DEBUG)
            self.mqtt_client.publish(self.MQTT_TOPIC_occupancy, f"{self.sensor_data['occupancy']}")

            if self.LOG_SENSOR_DATA == 1:
                self.write_to_json(self.LOG_SENSOR_DATA_FILE, self.sensor_data)

        except Exception as e:
            self.log.log_message("{}.post_sensor_data() {}".format(self.__class__.__name__, str(e)), LogLevel.ERROR)
        return None

    def read_sensor_data(self):
        try:
            self.log.log_message("{}.read_sensor_data() called ".format(self.__class__.__name__), LogLevel.DEBUG)
            self.sensor_data["distance"] = self.distance_sensor.read()  # read the distance in millimeters
            self.log.log_message("{} mm".format(str(self.sensor_data["distance"])), LogLevel.DEBUG)

            # if object detected within nominated distance
            self.sensor_data["occupancy"] = self.sensor_data["distance"] <= self.OCCUPANCY_DISTANCE
            if self.sensor_data["occupancy"] is True:
                self.log.log_message("Occupied", LogLevel.INFO)
            else:
                self.log.log_message("Vacant", LogLevel.INFO)
        except Exception as e:
            self.log.log_message(
                "ERROR: {}.read_sensor_data() {} ".format(self.__class__.__name__, str(e)),
                LogLevel.ERROR)
        return None
