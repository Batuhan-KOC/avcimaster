import threading
import socket
import logging

from SharedData import SharedData

logging.basicConfig(level=logging.INFO)

class UnityCommunicationController:
    """
    UnityCommunicationController handles the communication between the Unity environment and the Python controller.
    It manages the sending and receiving of messages to signal the start and stop of the Unity environment,
    as well as the initialization status.
    """

    def __init__(self):
        """
        Initializes the UnityCommunicationController, setting up the necessary sockets and starting the controller thread.
        """
        self._InitializeReceiveMessages()
        self._InitializeTransmitMessages()
        self._CreateAndStartControllerThread()
        
    def Terminate(self):
        """
        Terminates the UnityCommunicationController, stopping the controller thread and closing the sockets.
        """
        self._running = False
        self._thread.join()
        self._ReceiveSocket10006.close()
        self._TransmitSocket10003.close()

    def _CreateAndStartControllerThread(self):
        """
        Creates and starts the controller thread, which runs the main communication loop.
        """
        self._thread = threading.Thread(target=self._run)
        self._thread.daemon = True
        self._running = True
        self._thread.start()

    def _InitializeReceiveMessages(self):
        """
        Initializes the shared data objects for receiving messages from the Unity environment.
        """
        self._unityEnvironmentStartedMessageReceived = SharedData(False)
        self._unityEnvironmentStoppedMessageReceived = SharedData(False)
        self._unityInitializationReadyMessageReceived = SharedData(False)

    def _InitializeTransmitMessages(self):
        """
        Initializes the shared data objects for transmitting messages to the Unity environment.
        """
        self._sendStartUnityEnvironmentMessage = SharedData(False)
        self._sendStopUnityEnvironmentMessage = SharedData(False)

    def GetUnityEnvironmentStartedMessageReceived(self)->bool:
        """
        Gets the Unity environment started message status and resets it.

        Returns:
            bool: True if the Unity environment started message was received, False otherwise.
        """
        return self._unityEnvironmentStartedMessageReceived.GetAndSet(False)

    def GetUnityEnvironmentStoppedMessageReceived(self)->bool:
        """
        Gets the Unity environment stopped message status and resets it.

        Returns:
            bool: True if the Unity environment stopped message was received, False otherwise.
        """
        return self._unityEnvironmentStoppedMessageReceived.GetAndSet(False)

    def GetUnityInitializationReadyMessageReceived(self)->bool:
        """
        Gets the Unity initialization ready message status and resets it.

        Returns:
            bool: True if the Unity initialization ready message was received, False otherwise.
        """
        return self._unityInitializationReadyMessageReceived.GetAndSet(False)
    
    def SetSendStartUnityEnvironmentMessage(self):
        """
        Sets the flag to send the start Unity environment message.
        """
        return self._sendStartUnityEnvironmentMessage.Set(True)

    def SetSendStopUnityEnvironmentMessage(self):
        """
        Sets the flag to send the stop Unity environment message.
        """
        return self._sendStopUnityEnvironmentMessage.Set(True)

    def _Initialize10006ReceiveSocket(self):
        """
        Initializes the UDP socket for receiving messages from the Unity environment on port 10006.
        """
        self._ReceiveSocket10006 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._ReceiveSocket10006.bind(("0.0.0.0", 10006))
        self._ReceiveSocket10006.setblocking(False)

    def _Initialize10003TransmitSocket(self):
        """
        Initializes the UDP socket for transmitting messages to the Unity environment on port 10003.
        """
        self._TransmitSocket10003 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def _SendMessageFrom10003TransmitSocket(self, message: int):
        """
        Sends a message to the Unity environment using the transmit socket on port 10003.

        Args:
            message (int): The message to be sent.
        """
        # Ensure message is sent as bytes
        self._TransmitSocket10003.sendto(bytes([message]), ("127.0.0.1", 10003))

    def _Read10006ReceiveSocket(self):
        """
        Reads messages from the receive socket on port 10006 and updates the corresponding message received flags.
        """
        try:
            data, addr = self._ReceiveSocket10006.recvfrom(1)

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
        except Exception as e:
            logging.error(f"Error in _Read10006ReceiveSocket: {e}")

    def _ReadMessage(self):
        """
        Reads messages from the receive socket.
        """
        self._Read10006ReceiveSocket()

    def _SendMessageOnPort10003(self):
        """
        Sends messages to the Unity environment on port 10003 based on the set flags.
        """
        sendStartUnityEnvironmentMessage = self._sendStartUnityEnvironmentMessage.GetAndSet(False)
        sendStopUnityEnvironmentMessage = self._sendStopUnityEnvironmentMessage.GetAndSet(False)

        if sendStartUnityEnvironmentMessage:
            message = 0b00000001
            self._SendMessageFrom10003TransmitSocket(message)

        if sendStopUnityEnvironmentMessage:
            message = 0b00000010
            self._SendMessageFrom10003TransmitSocket(message)

    def _SendMessage(self):
        """
        Sends messages to the Unity environment.
        """
        self._SendMessageOnPort10003()

    def _run(self):
        """
        The main communication loop, running in the controller thread.
        Reads and sends messages in a loop while the controller is running.
        """
        self._Initialize10006ReceiveSocket()
        self._Initialize10003TransmitSocket()

        while(self._running):
            self._ReadMessage()
            self._SendMessage()

