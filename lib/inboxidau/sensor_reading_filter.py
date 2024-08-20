class DiscardExtremesFilter:

    # Discard Extremes
    # How it works: Remove just the highest and lowest readings in a window
    # of recent data points, then calculate the average of the remaining readings.
    # Implementation: Keep a sliding window of the last n readings, remove the
    # maximum and minimum, and calculate the mean of what's left.

    # Usage:
    # filter = DiscardExtremesFilter(window_size=5)
    # filtered_value = filter.add_reading(sensor_value)

    def __init__(self, window_size=5):
        self.window = []
        self.window_size = window_size

    def reset(self):
        # Resets the filter to its initial empty state.
        self.window = []

    def add_reading(self, value):
        if len(self.window) >= self.window_size:
            self.window.pop(0)
        self.window.append(value)

        if len(self.window) > 2:  # Ensure we have enough data to discard
            sorted_window = sorted(self.window)
            # Remove highest and lowest, then calculate mean
            trimmed_window = sorted_window[1:-1]
            return sum(trimmed_window) / len(trimmed_window)
        return value  # Return the value directly if not enough data


class TrimmedMeanFilter:

    # Trimmed Mean
    # How it works: A trimmed mean discards a certain percentage of the
    # highest and lowest values before calculating the mean of the remaining
    # values.

    # Implementation: You sort the readings, remove the top p% and bottom p%
    # of values, and then compute the average of the remaining values.

    # Usage:
    # filter = TrimmedMeanFilter(window_size=5, trim_percent=0.1)
    # filtered_value = filter.add_reading(sensor_value)

    def __init__(self, window_size=5, trim_percent=0.1):
        self.window = []
        self.window_size = window_size
        self.trim_percent = trim_percent

    def reset(self):
        # Resets the filter to its initial empty state.
        self.window = []

    def add_reading(self, value):
        # Maintain window of fixed size
        if len(self.window) >= self.window_size:
            self.window.pop(0)
        self.window.append(value)

        # Calculate trimmed mean if enough data
        if len(self.window) > 1:
            sorted_window = sorted(self.window)
            trim_count = int(len(sorted_window) * self.trim_percent)
            trimmed_window = sorted_window[trim_count:-trim_count] if trim_count else sorted_window
            return sum(trimmed_window) / len(trimmed_window)

        # Return value directly if not enough data
        return value
