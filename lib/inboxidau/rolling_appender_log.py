import os


class LogLevel:
    ERROR = 1
    DEBUG = 2
    INFO = 3


class LogOperationException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class URollingAppenderLog:
    def __init__(self, log_file, max_file_size_bytes=4 * 20,
                 max_backups=5, print_messages=False, log_level=LogLevel.INFO):
        # if log_level is set to LogLevel.DEBUG then the class will emit its own
        # debug information as "CONSOLE:" only to stdout
        if max_backups < 0:
            raise ValueError("max_backups must be greater than or equal to zero.")
        self.log_file = log_file
        self.max_file_size_bytes = max_file_size_bytes
        self.max_backups = max_backups
        self.print_messages = print_messages
        self.log_level = log_level

    def log_message(self, message, level=LogLevel.INFO, tid="0000-00-00T00:00:00Z"):
        display_message = False

        prefix_mapping = {
            LogLevel.INFO: "INFO",
            LogLevel.DEBUG: "DEBUG",
            LogLevel.ERROR: "ERROR"
        }

        prefix = prefix_mapping.get(level, "UNKNOWN")

        if level == LogLevel.ERROR or \
            (self.log_level == LogLevel.INFO and level == LogLevel.INFO) or \
                (self.log_level == LogLevel.DEBUG and level in (LogLevel.DEBUG, LogLevel.INFO)):
            display_message = True
        else:
            display_message = False

        message = f"TID:{tid}-{prefix}-{message}"

        if display_message is True:
            if self.print_messages is True:
                print(message)

            self.existing_backups = [f for f in os.listdir() if f.startswith(f"{self.log_file}.")]

            # Check if the log file exists and if its size exceeds the limit
            if self.log_file in os.listdir():
                log_file_size = os.stat(self.log_file)[6]  # Index 6 corresponds to the size in the os.stat result
                if log_file_size > self.max_file_size_bytes:
                    # Roll over backups if the maximum number is reached
                    self.roll_over_backups()

            try:
                # Open the log file in append mode and write the message
                with open(self.log_file, 'a') as file:
                    file.write(message + '\n')
            except OSError as e:
                error_message = f"Error during log_message() {e}"
                self._print_console_message(error_message)
                raise LogOperationException(error_message)

    def roll_over_backups(self):
        try:
            if self.max_backups == 0:
                self._delete_all_backups()
            else:
                self._remove_extra_backups()
                self._rename_existing_backups()
                self._rename_current_log_file()
                self._update_existing_backups_list()

        except OSError as e:
            self._handle_rotation_error(e)

        return self.existing_backups

    def _delete_all_backups(self):
        # Delete all existing backup files
        for backup_file in [f for f in os.listdir() if f.startswith(f"{self.log_file}.")]:
            self._print_console_message(f"remove {backup_file}")
            os.remove(backup_file)
        self.existing_backups = []

    def _remove_extra_backups(self):
        # Remove extra backups if the number exceeds max_backups
        while len(self.existing_backups) >= self.max_backups:
            largest_backup = max(self.existing_backups, key=lambda x: int(x.split('.')[-1]))
            self._print_console_message(f"remove {largest_backup}")
            os.remove(largest_backup)
            self.existing_backups.remove(largest_backup)

    def _rename_existing_backups(self):
        # Rename existing backups in descending order
        for backup_index in sorted(range(1, self._get_next_backup_index()), reverse=True):
            old_backup = f"{self.log_file}.{backup_index}"
            new_backup = f"{self.log_file}.{backup_index + 1}"
            self._print_console_message(f"rename {old_backup} to {new_backup}")
            os.rename(old_backup, new_backup)

    def _rename_current_log_file(self):
        # Rename the current log file
        self._print_console_message(f"rename {self.log_file} to {self.log_file}.1")
        os.rename(self.log_file, f"{self.log_file}.1")

    def _update_existing_backups_list(self):
        # Adjust the list of existing backups after renaming
        self.existing_backups = [f"{self.log_file}.{i}" for i in range(1, self._get_next_backup_index())]

    def _handle_rotation_error(self, e):
        error_message = f"Error during backup rotation: {e}"
        self._print_console_message(error_message)
        raise LogOperationException(error_message)

    def _get_next_backup_index(self):
        backup_index = 1

        while f"{self.log_file}.{backup_index}" in self.existing_backups:
            backup_index += 1
        if self.print_messages is True and self.log_level == LogLevel.DEBUG:
            print(f"CONSOLE: _get_next_backup_index = {backup_index}")
        return backup_index

    def _print_console_message(self, message):
        if self.print_messages and self.log_level == LogLevel.DEBUG:
            print(f"CONSOLE: {message}")
