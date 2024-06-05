from rolling_appender_log import URollingAppenderLog, LogLevel
from pico_w_sensor_node import UPicoWSensorNode
import time
from AtmosphericSensorNode import AtmosphericSensorNode

log = URollingAppenderLog("AtmosphericSensorNode.log", max_file_size_bytes=1024, max_backups=10, print_messages=True, log_level=AtmosphericSensorNode.STATIC_NODE_LOG_LEVEL)

myNode = AtmosphericSensorNode(log=log, config_path="config.json")

while True:
    try:
        print("CONSOLE: starting myNode")
        log.log_message("main.py starting myNode", LogLevel.INFO)
        myNode.main()
    except Exception as e:
        print(f"CONSOLE: exception in myNode ({e})")
        log.log_message(f"main.py {str(e)}", LogLevel.ERROR)
        
    print(f"CONSOLE: retry in {myNode.STATIC_NODE_RESTART_DELAY}.")
    log.log_message(f"main.py retry in {myNode.STATIC_NODE_RESTART_DELAY} seconds.", LogLevel.INFO)
    time.sleep(myNode.STATIC_NODE_RESTART_DELAY)