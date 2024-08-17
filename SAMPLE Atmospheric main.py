from lib.inboxidau.rolling_appender_log import URollingAppenderLog, LogLevel
import time
from AtmosphericSensorNode import AtmosphericSensorNode

log = URollingAppenderLog("AtmosphericSensorNode.log",
                          max_file_size_bytes=1024,
                          max_backups=10,
                          print_messages=True,
                          log_level=AtmosphericSensorNode.STATIC_NODE_LOG_LEVEL)  # noqa: E501

myNode = AtmosphericSensorNode(log=log, config_path="myconfig.json")

while True:
    try:
        print("CONSOLE: starting AtmosphericSensorNode myNode")
        log.log_message("main.py starting myNode", LogLevel.INFO)
        myNode.main()

    except Exception as e:
        print(f"CONSOLE: exception in AtmosphericSensorNode myNode ({e})")
        log.log_message(f"main.py {str(e)}", LogLevel.ERROR)

    print(f"CONSOLE: retry in {myNode.STATIC_NODE_RESTART_DELAY}.")

    log.log_message(f"main.py retry in {myNode.STATIC_NODE_RESTART_DELAY} seconds.", LogLevel.INFO)  # noqa: E501
    time.sleep(myNode.STATIC_NODE_RESTART_DELAY)
