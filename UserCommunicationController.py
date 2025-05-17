import threading
import socket

from SharedData import SharedData

class UserCommunicationController:
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
        self._userStartSimulationMessageReceived = SharedData(False)
        self._userStopSimulationMessageReceived = SharedData(False)
    
    def _InitializeTransmitMessages(self):
        self._sendSimulationStartedMessage = SharedData(False)
        self._sendSimulationStoppedMessage = SharedData(False)
  
    def GetUserStartSimulationMessageReceived(self)->bool:
        self._userStartSimulationMessageReceived.GetAndSet(False)
        
    def GetUserStopSimulationMessageReceived(self)->bool:
        self._userStopSimulationMessageReceived.GetAndSet(False)
        
    def SetSendSimulationStartedMessage(self):
        self._sendSimulationStartedMessage.Set(True)
    
    def SetSendSimulationStoppedMessage(self):
        self._sendSimulationStoppedMessage.Set(True)

    def Terminate(self):
        self._running = False
        self._thread.join()
        self._ReceiveSocket10002.close()
        self._TransmitSocket10001.close()

    def _Initialize10002ReceiveSocket(self):
        self._ReceiveSocket10002 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._ReceiveSocket10002.bind("0.0.0.0", 10002)
        self._ReceiveSocket10002.setblocking(False)
        
    def _Initialize10001TransmitSocket(self):
        self._TransmitSocket10001 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def _SendMessageFrom10001TransmitSocket(self, message):
        self._TransmitSocket10001.sendto(message, ("127.0.0.1", 10001))
        
    def _SendMessageOnPort10001(self):
        sendSimulationStartedMessage = self._sendSimulationStartedMessage.GetAndSet(False)
        sendSimulationStoppedMessage = self._sendSimulationStoppedMessage.GetAndSet(False)
        
        if sendSimulationStartedMessage:
            message = 0b00000001
            self._SendMessageFrom10001TransmitSocket(message)
        if sendSimulationStoppedMessage:
            message = 0b00000010
            self._SendMessageFrom10001TransmitSocket(message)

    def _Read10002ReceiveSocket(self):
        try:
            data, addr = self._ReceiveSocket10002.recvfrom(1)

            userSimulationStart = bool(data & 0b00000001)
            userSimulationStop = bool(data & 0b00000010)

            if userSimulationStart:
                self._userStartSimulationMessageReceived.Set(True)
            if userSimulationStop:
                self._userStopSimulationMessageReceived.Set(True)
        except BlockingIOError:
            pass # No data available
        
    def _ReadMessage(self):
        self._Read10002ReceiveSocket()
        
    def _SendMessage(self):
        self._SendMessageOnPort10001()

    def _run(self):
        self._Initialize10002ReceiveSocket()
        self._Initialize10001TransmitSocket()

        while(self._running):
            self._ReadMessage()
            self._SendMessage()