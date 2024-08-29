from lib.inboxidau.pico_w_sensor_node import UPicoWSensorNode
from lib.inboxidau.rolling_appender_log import LogLevel


class DistanceSensorNode(UPicoWSensorNode):

    # Used to designate the log level required, normally LogLevel.INF
    # will suffice for a completed device
    STATIC_NODE_LOG_LEVEL = LogLevel.INFO

    # Used to designate the delay in seconds between sensor reading
    STATIC_NODE_SENSE_REPEAT_DELAY = 5

    # Used to designate the number of sensor readings to filter
    # before submitting in the post method.
    STATIC_NODE_SENSE_FILTER_SIZE = 10

    STATIC_NODE_OCCUPANCY_HISTORY_SIZE = 3

    POST_SENSOR_DATA_FORMAT = "{}.post_sensor_data() {} to >{}"

    def __init__(self, log, config_path='UPicoWSensorNode.json'):
        super().__init__(log, config_path)
        if self.config:
            self.MQTT_TOPIC_distance = self.config.get(
                'MQTT_TOPIC_distance', '')
            self.MQTT_TOPIC_occupancy = self.config.get(
                'MQTT_TOPIC_occupancy', '')
            self.OCCUPANCY_DISTANCE = self.config.get(
                'OCCUPANCY_DISTANCE', '')
            self.log.log_message(
                f"{self.__class__.__name__} Config values applied",
                LogLevel.INFO)
        else:
            self.log.log_message(
                f"{self.__class__.__name__} Failed to load config file.",
                LogLevel.ERROR)

        self.log.log_message(
            f"{self.__class__.__name__} initialized.",
            LogLevel.DEBUG)

        from lib.PiicoDev_VL53L1X import PiicoDev_VL53L1X
        self.distance_sensor = PiicoDev_VL53L1X()  # initialise the sensor

        from lib.inboxidau.sensor_reading_filter import DiscardExtremesFilter
        self.filtered_distance_sensor = DiscardExtremesFilter(self.STATIC_NODE_SENSE_FILTER_SIZE)

        self.occupancy_history = []  # Stores the last few occupancy assessments
        self.sensor_data["occupancy"] = False
        self.sensor_data["distance"] = 0
        self.last_removed_occupancy = None  # Tracks the last removed occupancy state

    def post_sensor_data(self):
        try:
            self.log_message("post_sensor_data", LogLevel.INFO)

            log_message = self.POST_SENSOR_DATA_FORMAT.format(
                self.__class__.__name__,
                self.sensor_data["distance"],
                self.MQTT_TOPIC_distance
             )
            self.log_message(log_message, LogLevel.DEBUG)
            self.mqtt_client.publish(
                self.MQTT_TOPIC_distance,
                f"{self.sensor_data['distance']}")

            log_message = self.POST_SENSOR_DATA_FORMAT.format(
                self.__class__.__name__,
                self.sensor_data["occupancy"],
                self.MQTT_TOPIC_occupancy)

            self.log_message(log_message, LogLevel.DEBUG)
            self.mqtt_client.publish(
                self.MQTT_TOPIC_occupancy,
                f"{self.sensor_data['occupancy']}")

            if self.LOG_SENSOR_DATA == 1:
                self.write_to_json(self.LOG_SENSOR_DATA_FILE, self.sensor_data)

        except Exception as e:
            self.log.log_message(
                f"{self.__class__.__name__}.post_sensor_data() {str(e)}",
                LogLevel.ERROR)
        return None

    def update_occupancy_history(self, occupancy):
        # Updates the occupancy history with the latest assessment.
        # Save the last removed occupancy state before removing it.
        if len(self.occupancy_history) >= self.STATIC_NODE_OCCUPANCY_HISTORY_SIZE:
            self.last_removed_occupancy = self.occupancy_history.pop(0)
        self.occupancy_history.append(occupancy)

    def detect_occupancy_change(self):
        # Detects if there's a change in occupancy based on the last few assessments.
        if len(self.occupancy_history) < self.STATIC_NODE_OCCUPANCY_HISTORY_SIZE:
            self.log_message("Not enough data to assess a change in occupancy ", LogLevel.DEBUG)
            return False  # Not enough data to assess a change

        # Check if the last removed value is None
        if self.last_removed_occupancy is None:
            self.log_message("Not enough data popped to assess a change in occupancy ", LogLevel.DEBUG)
            return False  # Not enough change to assess a change

        # Check if all recent assessments are the same
        last_state = self.occupancy_history[-1]
        if not all(state == last_state for state in self.occupancy_history):
            self.log_message("No persistent change in historic occupancy", LogLevel.DEBUG)
            return False  # No change in occupancy

        # Check that the last popped value is not the same as the persistent value
        if self.last_removed_occupancy is not None and self.last_removed_occupancy == last_state:
            self.log_message("No change in historic occupancy", LogLevel.DEBUG)
            return False  # No change in occupancy

        # Otherwise, there has been a change
        self.log_message(f"There was a change in historic occupancy last_state:{last_state}  last_removed:{self.last_removed_occupancy}",  # noqa: E501
                         LogLevel.DEBUG)
        for index, item in enumerate(self.occupancy_history):
            print(f"Index {index}: {item}")

        return True

    def assess_occupancy(self, filtered_value):
        return filtered_value < self.OCCUPANCY_DISTANCE  # noqa: E501  True if occupied, False if not

    def read_sensor_data(self):
        try:
            self.log_message("read_sensor_data ", LogLevel.DEBUG)

            self.filtered_distance_sensor.reset()
            for _ in range(self.STATIC_NODE_SENSE_FILTER_SIZE):

                # read the distance in millimeters
                distance = self.distance_sensor.read()
                self.sensor_data["distance"] = self.filtered_distance_sensor.add_reading(distance)
                self.log.log_message(
                    f"{str(_)}: {str(self.sensor_data['distance'])} mm (last raw value: {str(distance)} mm)",
                    LogLevel.DEBUG)

            # Add the current occupancy assessment to the history
            occupancy_state = self.assess_occupancy(distance)
            self.update_occupancy_history(occupancy_state)
            self.log.log_message(f"{distance} {occupancy_state}", LogLevel.DEBUG)

            # Detect if there has been a consistent change in status according to history
            if self.detect_occupancy_change() is True:
                # if object detected within nominated distance
                self.sensor_data["occupancy"] = occupancy_state
                if self.sensor_data["occupancy"] is True:
                    self.log.log_message("Occupied", LogLevel.INFO)
                else:
                    self.log.log_message("Vacant", LogLevel.INFO)

        except Exception as e:
            self.log_message(
                f"ERROR: {self.__class__.__name__}.read_sensor_data() {str(e)}",  # noqa: E501
                LogLevel.ERROR)
        return None
