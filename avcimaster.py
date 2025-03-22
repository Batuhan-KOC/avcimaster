import threading
from enum import Enum
from UnityCommunicationController import UnityCommunicationController
from UserCommunicationController import UserCommunicationController

class AvciMaster:
    class State(Enum):
        WAITING_START_SIMULATION_MESSAGE_FROM_USER = 0
        SEND_START_UNITY_ENVIRONMENT_MESSAGE_TO_UNITY = 1
        WAITING_UNITY_ENVIRONMENT_STARTED_MESSAGE_FROM_UNITY = 2
        START_PX4_SITL_SIMULATION = 3

    def __init__(self):
        self.InitializeState()
        self.InitializeControllers()

    def InitializeState(self):
        self.state = self.State.WAITING_START_SIMULATION_MESSAGE_FROM_USER

    ####################################################################
    # MESSAGE INITIALIZERS
    ####################################################################
        
    def InitializeUnityCommunicationController(self):
        self.unityCommunicationController = UnityCommunicationController()

    def InitializeUserCommunicationController(self):
        self.userCommunicationController = UserCommunicationController()

    def InitializeControllers(self):
        self.InitializeUnityCommunicationController()
        self.InitializeUserCommunicationController()

    ####################################################################
    # C. UNITY PROCESS START STOP FUNCTIONS
    ####################################################################

    def StartUnityProcess(self):
        pass

    def StopUnityProcess(self):
        pass

    ####################################################################
    # D. OWN CLASS FUNCTIONS AND MEMBERS
    ####################################################################

    def WaitingStartSimulationMessageFromUserUpdate(self):
        userSimulationStartMessageReceived = self.userCommunicationController.GetUserStartSimulationMessageReceived()

        if userSimulationStartMessageReceived:
            self.state = self.State.SEND_START_UNITY_ENVIRONMENT_MESSAGE_TO_UNITY

    def SendStartUnityEnvironmentMessageToUnityUpdate(self):
        self.unityCommunicationController.SetSendStartUnityEnvironmentMessage()

        self.state = self.State.WAITING_UNITY_ENVIRONMENT_STARTED_MESSAGE_FROM_UNITY

    def WaitingUnityEnvironmentStartedMessageFromUnityUpdate(self):
        unityEnvironmentStartedMessageReceived = self.unityCommunicationController.GetUnityEnvironmentStartedMessageReceived()

        if unityEnvironmentStartedMessageReceived:
            self.state = self.State.START_PX4_SITL_SIMULATION

    def Update(self):
        unityInitializationReadyMessageReceived = False

        while not unityInitializationReadyMessageReceived:
            unityInitializationReadyMessageReceived = UnityCommunicationController.GetUnityInitializationReadyMessageReceived()
        
        while True:
            match self.state:
                case self.State.WAITING_START_SIMULATION_MESSAGE_FROM_USER:
                    self.WaitingStartSimulationMessageFromUserUpdate()
                case self.State.SEND_START_UNITY_ENVIRONMENT_MESSAGE_TO_UNITY:
                    self.SendStartUnityEnvironmentMessageToUnityUpdate()
                case self.State.WAITING_UNITY_ENVIRONMENT_STARTED_MESSAGE_FROM_UNITY:
                    self.WaitingUnityEnvironmentStartedMessageFromUnityUpdate()
                case self.State.START_PX4_SITL_SIMULATION:
                    pass # TODO

    def Terminate(self):
        pass


if __name__ == "__main__":
    avciMaster = AvciMaster()
    
    avciMaster.StartUnityProcess()

    while True:
        avciMaster.Update()
