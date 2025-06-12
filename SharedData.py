import threading

class SharedData:
    """Thread-safe shared data container."""
    def __init__(self, initialData=None):
        self.data = initialData
        self._mutex = threading.Lock()

    def Set(self, newValue):
        """Set the shared data to a new value."""
        with self._mutex:
            self.data = newValue

    def Get(self):
        """Get a copy of the shared data."""
        with self._mutex:
            return self.data

    def GetAndSet(self, newValue):
        """Get the current value and set a new value atomically."""
        with self._mutex:
            copy = self.data
            self.data = newValue
            return copy