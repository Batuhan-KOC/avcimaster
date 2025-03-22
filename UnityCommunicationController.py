import threading
import socket

from SharedData import SharedData

class UnityCommunicationController:
    def __init__(self):
        self._InitializeReceiveMessages()
        self._InitializeTransmitMessages()
        self._CreateAndStartControllerThread()

    def _CreateAndStartControllerThread(self):
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._running = True
        self._thread.start()

    def _InitializeReceiveMessages(self):
        self._unityEnvironmentStartedMessageReceived = SharedData(False)
        self._unityEnvironmentStoppedMessageReceived = SharedData(False)
        self._unityInitializationReadyMessageReceived = SharedData(False)

    def _InitializeTransmitMessages(self):
        self._sendStartUnityEnvironmentMessage = SharedData(False)
        self._sendStopUnityEnvironmentMessage = SharedData(False)

    def GetUnityEnvironmentStartedMessageReceived(self)->bool:
        return self._unityEnvironmentStartedMessageReceived.GetAndSet(False)

    def GetUnityEnvironmentStoppedMessageReceived(self)->bool:
        return self._unityEnvironmentStoppedMessageReceived.GetAndSet(False)

    def GetUnityInitializationReadyMessageReceived(self)->bool:
        return self._unityInitializationReadyMessageReceived.GetAndSet(False)
    
    def SetSendStartUnityEnvironmentMessage(self):
        return self._sendStartUnityEnvironmentMessage.Set(True)

    def SetSendStopUnityEnvironmentMessage(self):
        return self._sendStopUnityEnvironmentMessage.Set(True)

    def Terminate(self):
        self._running = False

    def _Initialize10006ReceiveSocket(self):
        self._Socket10006 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._Socket10006.bind("0.0.0.0", 10006)
        self._Socket10006.setblocking(False)

    def _Initialize10003TransmitSocket(self):
        self._Socket10003 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _SendMessageFrom10003TransmitSocket(self, message):
        self._Socket10003.sendto(message, ("127.0.0.1", 10003))

    def _Read10006ReceiveSocket(self):
        try:
            data, addr = self._Socket10006.recvfrom(1)

            unityEnvironmentStarted = bool(data & 0b00000001)
            unityEnvironmentStopped = bool(data & 0b00000010)
            unityEnvironmentInitializationReady = bool(data & 0b00000100)

            if unityEnvironmentStarted:
                self._unityEnvironmentStartedMessageReceived.Set(True)
            if unityEnvironmentStopped:
                self._unityEnvironmentStoppedMessageReceived.Set(True)
            if unityEnvironmentInitializationReady:
                self._unityInitializationReadyMessageReceived.Set(True)
        except BlockingIOError:
            pass # No data available

    def _ReadMessage(self):
        self._Read10006ReceiveSocket()

    def _SendMessageOnPort10003(self):
        sendStartUnityEnvironmentMessage = self._sendStartUnityEnvironmentMessage.GetAndSet(False)
        sendStopUnityEnvironmentMessage = self._sendStopUnityEnvironmentMessage.GetAndSet(False)

        if sendStartUnityEnvironmentMessage:
            message = 0b00000001
            self._SendMessageFrom10003TransmitSocket(message)

        if sendStopUnityEnvironmentMessage:
            message = 0b00000010
            self._SendMessageFrom10003TransmitSocket(message)

    def _SendMessage(self):
        self._SendMessageOnPort10003()

    def _run(self):
        self._Initialize10003TransmitSocket()
        self._Initialize10006ReceiveSocket()

        while(self._running):
            self._ReadMessage()
            self._SendMessage()

    