import time
from enum import Enum
from UnityCommunicationController import UnityCommunicationController
from UserCommunicationController import UserCommunicationController
from PX4SITLProcessController import PX4SITLProcessController

class AvciMaster:
    """
    Main controller for managing the simulation lifecycle and communication between Unity, PX4 SITL, and the user.
    """
    class State(Enum):
        IDLE = 0
        WAITING_START_SIMULATION_MESSAGE_FROM_USER = 1
        SEND_START_UNITY_ENVIRONMENT_MESSAGE_TO_UNITY = 2
        WAITING_UNITY_ENVIRONMENT_STARTED_MESSAGE_FROM_UNITY = 3
        START_PX4_SITL_SIMULATION = 4
        SEND_SIMULATION_STARTED_MESSAGE_TO_USER = 5
        WAITING_STOP_SIMULATION_MESSAGE_FROM_USER = 6
        STOP_PX4_SITL_SIMULATION = 7
        SEND_STOP_UNITY_ENVIRONMENT_MESSAGE_TO_UNITY = 8
        WAITING_UNITY_ENVIRONMENT_STOPPED_MESSAGE_FROM_UNITY = 9
        SEND_SIMULATION_STOPPED_MESSAGE_TO_USER = 10

    def __init__(self):
        """Initialize state and controllers."""
        self._terminated = False
        self.InitializeState()
        self.InitializeControllers()

    def InitializeState(self):
        self.SetState(self.State.IDLE)

    ####################################################################
    # MESSAGE INITIALIZERS
    ####################################################################
        
    def InitializeUnityCommunicationController(self):
        self.unityCommunicationController = UnityCommunicationController()

    def InitializeUserCommunicationController(self):
        self.userCommunicationController = UserCommunicationController()
        
    def InitializePX4SITLProcessController(self):
        self.px4SitlProcessController = PX4SITLProcessController()
        self.px4SitlProcessController.SetProcessErrorCallback(self.Px4SitlErrorCallback)

    def InitializeControllers(self):
        self.InitializeUnityCommunicationController()
        self.InitializeUserCommunicationController()
        self.InitializePX4SITLProcessController()

    ####################################################################
    # C. UNITY AND PX4 FUNCTIONS
    ####################################################################

    def StartUnityProcess(self):
        pass

    def StopUnityProcess(self):
        pass
    
    def Px4SitlErrorCallback(self):
        self.SetState(self.State.STOP_PX4_SITL_SIMULATION)

    ####################################################################
    # D. OWN CLASS FUNCTIONS AND MEMBERS
    ####################################################################

    def WaitingStartSimulationMessageFromUserUpdate(self):
        userSimulationStartMessageReceived = self.userCommunicationController.GetUserStartSimulationMessageReceived()

        if userSimulationStartMessageReceived:
            self.SetState(self.State.SEND_START_UNITY_ENVIRONMENT_MESSAGE_TO_UNITY)

    def SendStartUnityEnvironmentMessageToUnityUpdate(self):
        self.unityCommunicationController.SetSendStartUnityEnvironmentMessage()

        self.SetState(self.State.WAITING_UNITY_ENVIRONMENT_STARTED_MESSAGE_FROM_UNITY)

    def WaitingUnityEnvironmentStartedMessageFromUnityUpdate(self):
        unityEnvironmentStartedMessageReceived = self.unityCommunicationController.GetUnityEnvironmentStartedMessageReceived()

        if unityEnvironmentStartedMessageReceived:
            self.SetState(self.State.START_PX4_SITL_SIMULATION)
            
    def StartPx4SitlSimulationUpdate(self):
        sitlProcessControllerState = self.px4SitlProcessController.GetState()
        
        if sitlProcessControllerState is PX4SITLProcessController.State.IDLE:
            self.px4SitlProcessController.StartSITL()
        
        if sitlProcessControllerState is PX4SITLProcessController.State.STARTED:
            self.SetState(self.State.SEND_SIMULATION_STARTED_MESSAGE_TO_USER)
            
    def SendSimulationStartedMessageToUserUpdate(self):
        self.userCommunicationController.SetSendSimulationStartedMessage()
        self.SetState(self.State.WAITING_STOP_SIMULATION_MESSAGE_FROM_USER)
            
    def WaitingStopSimulationMessageFromUserUpdate(self):
        userSimulationStopMessageReceived = self.userCommunicationController.GetUserStopSimulationMessageReceived()

        if userSimulationStopMessageReceived:
            self.SetState(self.State.STOP_PX4_SITL_SIMULATION)
            
    def StopPx4SitlSimulationUpdate(self):
        self.px4SitlProcessController.StopSITL()
        
        self.SetState(self.State.SEND_STOP_UNITY_ENVIRONMENT_MESSAGE_TO_UNITY)
        
    def SendStopUnityEnvironmentMessageToUnityUpdate(self):
        self.unityCommunicationController.SetSendStopUnityEnvironmentMessage()
        
        self.SetState(self.State.WAITING_UNITY_ENVIRONMENT_STOPPED_MESSAGE_FROM_UNITY)
        
    def WaitingUnityEnvironmentStoppedMessageFromUnityUpdate(self):
        unityEnvironmentStoppedMessageReceived = self.unityCommunicationController.GetUnityEnvironmentStoppedMessageReceived()

        if unityEnvironmentStoppedMessageReceived:
            self.SetState(self.State.SEND_SIMULATION_STOPPED_MESSAGE_TO_USER)
            
    def SendSimulationStoppedMessageToUser(self):
        self.userCommunicationController.SetSendSimulationStoppedMessage()
        self.SetState(self.State.WAITING_START_SIMULATION_MESSAGE_FROM_USER)
        
    def Terminate(self):
        """
        Terminates all controllers and stops the Unity process.
        """
        if self._terminated:
            return
        self._terminated = True
        self.px4SitlProcessController.Terminate()
        self.unityCommunicationController.Terminate()
        self.userCommunicationController.Terminate()
        self.StopUnityProcess()

    def SetState(self, state: 'AvciMaster.State'):
        """
        Set the current state and print its name.
        Args:
            state (AvciMaster.State): The new state to set.
        """
        self.state = state
        print(f"State changed to: {state.name}")

    def Update(self):
        """
        Main update loop for the AvciMaster state machine.
        Waits for Unity initialization, then processes state transitions.
        """
        unityInitializationReadyMessageReceived = False

        print("Waiting for Unity initialization ready message.")
        while not unityInitializationReadyMessageReceived:
            unityInitializationReadyMessageReceived = self.unityCommunicationController.GetUnityInitializationReadyMessageReceived()
            if unityInitializationReadyMessageReceived:
                print("Unity initialization ready message received.")
                self.SetState(self.State.WAITING_START_SIMULATION_MESSAGE_FROM_USER)
            # Avoid busy waiting
            time.sleep(0.1)

        while True:
            match self.state:
                case self.State.WAITING_START_SIMULATION_MESSAGE_FROM_USER:
                    self.WaitingStartSimulationMessageFromUserUpdate()
                case self.State.SEND_START_UNITY_ENVIRONMENT_MESSAGE_TO_UNITY:
                    self.SendStartUnityEnvironmentMessageToUnityUpdate()
                case self.State.WAITING_UNITY_ENVIRONMENT_STARTED_MESSAGE_FROM_UNITY:
                    self.WaitingUnityEnvironmentStartedMessageFromUnityUpdate()
                case self.State.START_PX4_SITL_SIMULATION:
                    self.StartPx4SitlSimulationUpdate()
                case self.State.SEND_SIMULATION_STARTED_MESSAGE_TO_USER:
                    self.SendSimulationStartedMessageToUserUpdate()
                case self.State.WAITING_STOP_SIMULATION_MESSAGE_FROM_USER:
                    self.WaitingStopSimulationMessageFromUserUpdate()
                case self.State.STOP_PX4_SITL_SIMULATION:
                    self.StopPx4SitlSimulationUpdate()
                case self.State.SEND_STOP_UNITY_ENVIRONMENT_MESSAGE_TO_UNITY:
                    self.SendStopUnityEnvironmentMessageToUnityUpdate()
                case self.State.WAITING_UNITY_ENVIRONMENT_STOPPED_MESSAGE_FROM_UNITY:
                    self.WaitingUnityEnvironmentStoppedMessageFromUnityUpdate()
                case self.State.SEND_SIMULATION_STOPPED_MESSAGE_TO_USER:
                    self.SendSimulationStoppedMessageToUser()
            time.sleep(0.1)

if __name__ == "__main__":
    avciMaster = AvciMaster()
    
    print("Staring unity.")
    avciMaster.StartUnityProcess()
    print("Unity process started successfully.")

    try:
        print("Starting avci master.")
        while True:
            avciMaster.Update()
    except KeyboardInterrupt:
        print("Terminating avci master.")
        avciMaster.Terminate()
        
    print("Avci master process finished successfully.")
