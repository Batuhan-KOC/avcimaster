import threading
import socket

class UserCommunicationController:
    def __init__(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._running = True

        self._thread.start()

    def _InitializeMessagesAndMutexes(self):
        self._userStartSimulationMessageReceivedMutex = threading.Lock()
        self._userStartSimulationMessageReceived = False

        self._userStopSimulationMessageReceivedMutex = threading.Lock()
        self._userStopSimulationMessageReceived = False

    def _SetUserStartSimulationMessageReceived(self):
        self._userStartSimulationMessageReceivedMutex.acquire()
        self._userStartSimulationMessageReceived = True
        self._userStartSimulationMessageReceivedMutex.release()

    def _SetUserStopSimulationMessageReceived(self):
        self._userStopSimulationMessageReceivedMutex.acquire()
        self._userStopSimulationMessageReceived = True
        self._userStopSimulationMessageReceivedMutex.release()

    def GetUserStartSimulationMessageReceived(self):
        self._userStartSimulationMessageReceivedMutex.acquire()
        value = self._userStartSimulationMessageReceived
        self._userStartSimulationMessageReceived = False
        self._userStartSimulationMessageReceivedMutex.release()
        return value

    def GetUserStopSimulationMessageReceived(self):
        self._userStopSimulationMessageReceivedMutex.acquire()
        value = self._userStopSimulationMessageReceived
        self._userStopSimulationMessageReceived = False
        self._userStopSimulationMessageReceivedMutex.release()
        return value

    def Terminate(self):
        self._running = False

    def _Initialize10002Socket(self):
        self._Socket10002 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._Socket10002.bind("0.0.0.0", 10002)
        self._Socket10002.setblocking(False)

    def _Read10002Socket(self):
        try:
            data, addr = self._Socket10002.recvfrom(1)

            userSimulationStart = bool(data & 0b00000001)
            userSimulationStop = bool(data & 0b00000010)

            if userSimulationStart:
                self._SetUserStartSimulationMessageReceived()
            if userSimulationStop:
                self._SetUserStopSimulationMessageReceived()
        except BlockingIOError:
            pass # No data available

    def _run(self):
        self._Initialize10002Socket()

        while(self._running):
            self._Read10002Socket()