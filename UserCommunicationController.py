import threading
import socket

from SharedData import SharedData

class UserCommunicationController:
    """Handles communication with the user for starting and stopping simulations."""
    
    def __init__(self):
        """Initializes the communication controller, setting up message receive/transmit mechanisms and starting the controller thread."""
        self._InitializeReceiveMessages()
        self._InitializeTransmitMessages()
        self._CreateAndStartControllerThread()
        
    def _CreateAndStartControllerThread(self):
        """Creates and starts the controller thread responsible for handling communication."""
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._running = True
        self._thread.start()
        
    def _InitializeReceiveMessages(self):
        """Initializes the mechanisms for receiving messages from the user."""
        self._userStartSimulationMessageReceived = SharedData(False)
        self._userStopSimulationMessageReceived = SharedData(False)
    
    def _InitializeTransmitMessages(self):
        """Initializes the mechanisms for transmitting messages to the user."""
        self._sendSimulationStartedMessage = SharedData(False)
        self._sendSimulationStoppedMessage = SharedData(False)
  
    def GetUserStartSimulationMessageReceived(self) -> bool:
        """Checks and returns the status of the user start simulation message.

        Returns:
            bool: True if the start simulation message was received, False otherwise.
        """
        return self._userStartSimulationMessageReceived.GetAndSet(False)

    def GetUserStopSimulationMessageReceived(self) -> bool:
        """Checks and returns the status of the user stop simulation message.

        Returns:
            bool: True if the stop simulation message was received, False otherwise.
        """
        return self._userStopSimulationMessageReceived.GetAndSet(False)
        
    def SetSendSimulationStartedMessage(self):
        """Sets the flag to send the simulation started message to the user."""
        self._sendSimulationStartedMessage.Set(True)
    
    def SetSendSimulationStoppedMessage(self):
        """Sets the flag to send the simulation stopped message to the user."""
        self._sendSimulationStoppedMessage.Set(True)

    def Terminate(self):
        """Terminates the communication controller, stopping the controller thread and closing sockets."""
        self._running = False
        self._thread.join()
        self._ReceiveSocket10002.close()
        self._TransmitSocket10001.close()

    def _Initialize10002ReceiveSocket(self):
        """Initialises the UDP socket for receiving messages on port 10002."""
        self._ReceiveSocket10002 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._ReceiveSocket10002.bind(("0.0.0.0", 10002))
        self._ReceiveSocket10002.setblocking(False)
        
    def _Initialize10001TransmitSocket(self):
        """Initializes the UDP socket for transmitting messages on port 10001."""
        self._TransmitSocket10001 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def _SendMessageFrom10001TransmitSocket(self, message: int):
        """Sends a message using the transmit socket on port 10001.

        Args:
            message (int): The message to be sent.
        """
        # Ensure message is sent as bytes
        self._TransmitSocket10001.sendto(bytes([message]), ("127.0.0.1", 10001))
        
    def _SendMessageOnPort10001(self):
        """Sends the appropriate message on port 10001 based on the current simulation state."""
        sendSimulationStartedMessage = self._sendSimulationStartedMessage.GetAndSet(False)
        sendSimulationStoppedMessage = self._sendSimulationStoppedMessage.GetAndSet(False)
        
        if sendSimulationStartedMessage:
            message = 0b00000001
            self._SendMessageFrom10001TransmitSocket(message)
        if sendSimulationStoppedMessage:
            message = 0b00000010
            self._SendMessageFrom10001TransmitSocket(message)

    def _Read10002ReceiveSocket(self):
        """Reads and processes messages from the receive socket on port 10002."""
        try:
            data, addr = self._ReceiveSocket10002.recvfrom(1)
            data = int.from_bytes(data, byteorder='big')

            userSimulationStart = bool(data & 0b00000001)
            userSimulationStop = bool(data & 0b00000010)

            if userSimulationStart:
                self._userStartSimulationMessageReceived.Set(True)
            if userSimulationStop:
                self._userStopSimulationMessageReceived.Set(True)
        except BlockingIOError:
            pass # No data available
        
    def _ReadMessage(self):
        """Reads incoming messages from the user."""
        self._Read10002ReceiveSocket()
        
    def _SendMessage(self):
        """Sends messages to the user based on the simulation state."""
        self._SendMessageOnPort10001()

    def _run(self):
        """The main loop of the controller thread, handling message reading and sending."""
        self._Initialize10002ReceiveSocket()
        self._Initialize10001TransmitSocket()

        while(self._running):
            self._ReadMessage()
            self._SendMessage()