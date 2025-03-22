import threading

class SharedData:
    def __init__(self, initialData = None):
        self.data = initialData
        self._mutex = threading.Lock()

    def Set(self, newValue):
        self._mutex.acquire()
        self.data = newValue
        self._mutex.release()

    def Get(self):
        self._mutex.acquire()
        copy = self.data
        self._mutex.release()
        return copy
    
    def GetAndSet(self, newValue):
        self._mutex.acquire()
        copy = self.data
        self.data = newValue
        self._mutex.release()
        return copy