import os
import sys
import unittest
import logging
from unittest.mock import patch, MagicMock, mock_open, Mock

# Mock the modules that are not available on a PC
sys.modules['ujson'] = Mock()
sys.modules['ubinascii'] = Mock()
sys.modules['machine'] = Mock()
sys.modules['network'] = Mock()
sys.modules['umqtt.robust'] = Mock()
sys.modules['ntptime'] = Mock()
sys.modules['utime'] = Mock()

# Import standard modules
import json
import binascii

# Insert the path to the module under test
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from rolling_appender_log import URollingAppenderLog, LogLevel
from pico_w_sensor_node import UPicoWSensorNode

class TestUPicoWSensorNode(unittest.TestCase):

    def setUp(self):
        log= logging.getLogger( "TestUPicoWSensorNode" )
        log.debug( "Enter setUp" )
        self.mock_log = MagicMock(spec=URollingAppenderLog)
        self.mock_mqtt_client = MagicMock()
        sys.modules['pico_w_sensor_node'].MQTTClient = MagicMock(return_value=self.mock_mqtt_client)
        # Mock utime.localtime() to return a predefined time tuple
        expected_time = (2024, 6, 4, 12, 30, 0, 0, 0)
        with unittest.mock.patch('utime.localtime', return_value=expected_time):
            self.node = UPicoWSensorNode(log=self.mock_log, config_path='test_config.json')
        log.debug( "Exit setUp" )


    def test_load_config(self):
        log= logging.getLogger( "TestUPicoWSensorNode" )
        log.debug( "Enter test_load_config" )
        expected_time = (2024, 6, 4, 12, 30, 0, 0, 0)
        with unittest.mock.patch('utime.localtime', return_value=expected_time):
            #config = self.node.load_config('test_config.json')
            log.debug( "test_load_config config= %r",  self.node.config )
            guid = self.node.generate_guid()
            log.debug( "test_load_config guid= %r",  self.node.guid )

        self.assertEqual(self.node.config, {
            "WIFI_SSID": "test 2.4 Ghz SID",
            "WIFI_PASSWORD": "test WiFi Password",
            "MQTT_BROKER": "test homebridge.local",
            "MQTT_PORT": 8883,
            "MQTT_TOPIC_temperature": "test/weatherstn/picodev_board/temperature",
            "MQTT_TOPIC_humidity": "test/weatherstn/picodev_board/humidity",
            "MQTT_TOPIC_airPressure": "test/weatherstn/picodev_board/airPressure",
            "MQTT_USERNAME": "test MQTT username",
            "MQTT_PASSWORD": "test MQTT password",
            "MQTT_CA_CERTS": "test MQTT.crt file",
            "MAKERVERSE_NANO_POWER_TIMER_HAT": "False"
        })
        log.debug( "Exit test_load_config" )

    @patch('pico_w_sensor_node.ujson.load', return_value=
           {
            "WIFI_SSID": "test 2.4 Ghz SID",
            "WIFI_PASSWORD": "test WiFi Password",
            "MQTT_BROKER": "test homebridge.local",
            "MQTT_PORT": 8883,
            "MQTT_TOPIC_temperature": "test/weatherstn/picodev_board/temperature",
            "MQTT_TOPIC_humidity": "test/weatherstn/picodev_board/humidity",
            "MQTT_TOPIC_airPressure": "test/weatherstn/picodev_board/airPressure",
            "MQTT_USERNAME": "test MQTT username",
            "MQTT_PASSWORD": "test MQTT password",
            "MQTT_CA_CERTS": "test MQTT.crt file",
            "MAKERVERSE_NANO_POWER_TIMER_HAT": "False"
        })
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_mocked_load_config(self, mock_open, mock_ujson_load):
        log= logging.getLogger( "TestUPicoWSensorNode" )
        log.debug( "Enter test_mocked_load_config" )
        expected_time = (2024, 6, 4, 12, 30, 0, 0, 0)
        with unittest.mock.patch('utime.localtime', return_value=expected_time):
            config = self.node.load_config('test_config.json')
            log.debug( "test_mocked_load_config= %r", config )

        mock_open.assert_called_once_with('test_config.json', 'r')
        mock_ujson_load.assert_called_once_with(mock_open())
        self.assertEqual(config, {
            "WIFI_SSID": "test 2.4 Ghz SID",
            "WIFI_PASSWORD": "test WiFi Password",
            "MQTT_BROKER": "test homebridge.local",
            "MQTT_PORT": 8883,
            "MQTT_TOPIC_temperature": "test/weatherstn/picodev_board/temperature",
            "MQTT_TOPIC_humidity": "test/weatherstn/picodev_board/humidity",
            "MQTT_TOPIC_airPressure": "test/weatherstn/picodev_board/airPressure",
            "MQTT_USERNAME": "test MQTT username",
            "MQTT_PASSWORD": "test MQTT password",
            "MQTT_CA_CERTS": "test MQTT.crt file",
            "MAKERVERSE_NANO_POWER_TIMER_HAT": "False"
        })
        log.debug( "Exit test_mocked_load_config" )

if __name__ == '__main__':
    logging.basicConfig( stream=sys.stderr )
    logging.getLogger( "TestUPicoWSensorNode" ).setLevel( logging.DEBUG )
    unittest.main()
