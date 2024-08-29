from lib.inboxidau.rolling_appender_log import URollingAppenderLog, LogLevel
import time
from DistanceSensorNode import DistanceSensorNode

log = URollingAppenderLog("DistanceSensorNode.log", max_file_size_bytes=4096,
                          max_backups=10, print_messages=True,
                          log_level=DistanceSensorNode.STATIC_NODE_LOG_LEVEL)

myNode = DistanceSensorNode(log=log, config_path="config.json")

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
