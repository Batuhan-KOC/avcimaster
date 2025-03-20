import threading
import socket

class UnityCommunicationController:
    def __init__(self):
        self._InitializeReceiveMessagesAndMutexes()

        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._running = True

        self._thread.start()

    def _InitializeReceiveMessagesAndMutexes(self):
        self._unityEnvironmentStartedMessageReceivedMutex = threading.Lock()
        self._unityEnvironmentStartedMessageReceived = False

        self._unityEnvironmentStoppedMessageReceivedMutex = threading.Lock()
        self._unityEnvironmentStoppedMessageReceived = False

        self._unityInitializationReadyMessageReceivedMutex = threading.Lock()
        self._unityInitializationReadyMessageReceived = False

    def _InitializeTransmitMessagesAndMutexes(self):
        self._sendStartUnityEnvironmentMessageMutex = threading.Lock()
        self._sendStartUnityEnvironmentMessage = False

        self._sendStopUnityEnvironmentMessageMutex = threading.Lock()
        self._sendStopUnityEnvironmentMessage = False

    def _SetUnityEnvironmentStartedMessageReceived(self):
        self._unityEnvironmentStartedMessageReceivedMutex.acquire()
        self._unityEnvironmentStartedMessageReceived = True
        self._unityEnvironmentStartedMessageReceivedMutex.release()

    def _SetUnityEnvironmentStoppedMessageReceived(self):
        self._unityEnvironmentStoppedMessageReceivedMutex.acquire()
        self._unityEnvironmentStoppedMessageReceived = True
        self._unityEnvironmentStoppedMessageReceivedMutex.release()

    def _SetUnityInitializationReadyMessageReceived(self):
        self._unityInitializationReadyMessageReceivedMutex.acquire()
        self._unityInitializationReadyMessageReceived = True
        self._unityInitializationReadyMessageReceivedMutex.release()

    def GetUnityEnvironmentStartedMessageReceived(self)->bool:
        self._unityEnvironmentStartedMessageReceivedMutex.acquire()
        value = self._unityEnvironmentStartedMessageReceived
        self._unityEnvironmentStartedMessageReceived = False
        self._unityEnvironmentStartedMessageReceivedMutex.release()
        return value

    def GetUnityEnvironmentStoppedMessageReceived(self)->bool:
        self._unityEnvironmentStoppedMessageReceivedMutex.acquire()
        value = self._unityEnvironmentStoppedMessageReceived
        self._unityEnvironmentStoppedMessageReceived = False
        self._unityEnvironmentStoppedMessageReceivedMutex.release()
        return value

    def GetUnityInitializationReadyMessageReceived(self)->bool:
        self._unityInitializationReadyMessageReceivedMutex.acquire()
        value = self._unityInitializationReadyMessageReceived
        self._unityInitializationReadyMessageReceived = False
        self._unityInitializationReadyMessageReceivedMutex.release()
        return value
    
    def SetSendStartUnityEnvironmentMessage(self):
        self._sendStartUnityEnvironmentMessageMutex.acquire()
        self._sendStartUnityEnvironmentMessage = True
        self._sendStartUnityEnvironmentMessageMutex.release()

    def SetSendStopUnityEnvironmentMessage(self):
        self._sendStopUnityEnvironmentMessageMutex.acquire()
        self._sendStopUnityEnvironmentMessage = True
        self._sendStopUnityEnvironmentMessageMutex.release()

    def _GetSendStartUnityEnvironmentMessage(self):
        self._sendStartUnityEnvironmentMessageMutex.acquire()
        value = self._sendStartUnityEnvironmentMessage
        self._sendStartUnityEnvironmentMessage = False
        self._sendStartUnityEnvironmentMessageMutex.release()
        return value

    def _GetSendStopUnityEnvironmentMessage(self):
        self._sendStopUnityEnvironmentMessageMutex.acquire()
        value = self._sendStopUnityEnvironmentMessage
        self._sendStopUnityEnvironmentMessage = False
        self._sendStopUnityEnvironmentMessageMutex.release()
        return value

    def Terminate(self):
        self._running = False

    def _Initialize10006Socket(self):
        self._Socket10006 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._Socket10006.bind("0.0.0.0", 10006)
        self._Socket10006.setblocking(False)

    def _Initialize10003Socket(self):
        self._Socket10003 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _SendMessageFrom10003Socket(self, message):
        self._Socket10003.sendto(message, ("127.0.0.1", 10003))

    def _Read10006Socket(self):
        try:
            data, addr = self._Socket10006.recvfrom(1)

            unityEnvironmentStarted = bool(data & 0b00000001)
            unityEnvironmentStopped = bool(data & 0b00000010)
            unityEnvironmentInitializationReady = bool(data & 0b00000100)

            if unityEnvironmentStarted:
                self._SetUnityEnvironmentStartedMessageReceived()
            if unityEnvironmentStopped:
                self._SetUnityEnvironmentStoppedMessageReceived()
            if unityEnvironmentInitializationReady:
                self._SetUnityInitializationReadyMessageReceived()
        except BlockingIOError:
            pass # No data available

    def _ReadMessage(self):
        self._Read10006Socket()

    def _SendMessageOnPort10003(self):
        sendStartUnityEnvironmentMessage = self._GetSendStartUnityEnvironmentMessage()
        sendStopUnityEnvironmentMessage = self._GetSendStopUnityEnvironmentMessage()

        if sendStartUnityEnvironmentMessage:
            message = 0b00000001
            self._SendMessageFrom10003Socket(message)

        if sendStopUnityEnvironmentMessage:
            message = 0b00000010
            self._SendMessageFrom10003Socket(message)

    def _SendMessage(self):
        self._SendMessageOnPort10003()

    def _run(self):
        self._Initialize10003Socket()
        self._Initialize10006Socket()

        while(self._running):
            self._ReadMessage()
            self._SendMessage()

    