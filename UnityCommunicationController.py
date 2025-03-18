import threading
import socket

class UnityCommunicationController:
    def __init__(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._running = True

        self._thread.start()

    def Terminate(self):
        self._running = False

    def SetUnityInitializationReadyMessageCallback(self, callback):
        self._unityInitializationReadyMessageCallback = callback

    def SetUnityEnvironmentStartedMessageCallback(self, callback):
        self._unityEnvironmentStartedMessageCallback = callback

    def SetUnityEnvironmentStoppedMessageCallback(self, callback):
        self._unityEnvironmentStoppedMessageCallback = callback

    def _Initialize10006Socket(self):
        self.Socket10006 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.Socket10006.bind("0.0.0.0", 10006)
        self.Socket10006.setblocking(False)

    def _Read10006Socket(self):
        try:
            data, addr = self.Socket10006.recvfrom(1)

            unityEnvironmentStarted                 = bool(data & 0b00000001)
            unityEnvironmentStopped                 = bool(data & 0b00000010)
            unityEnvironmentInitializationReady     = bool(data & 0b00000100)

            if unityEnvironmentStarted:
                self._unityEnvironmentStartedMessageCallback()
            if unityEnvironmentStopped:
                self._unityEnvironmentStoppedMessageCallback()
            if unityEnvironmentInitializationReady:
                self._unityInitializationReadyMessageCallback()
        except BlockingIOError:
            pass # No data available

    def _run(self):
        self._Initialize10006Socket()

        while(self._running):
            self._Read10006Socket()

    