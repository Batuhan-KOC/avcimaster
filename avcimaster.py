from UnityCommunicationController import UnityCommunicationController

class AvciMaster:
    def __init__(self):
        self.unityStarted = False
        self.unityInitializationReadyMessageReceived = False
        self.unityEnvironmentStartedMessageReceived = False
        self.unityEnvironmentStoppedMessageReceived = False

        self.InitializeControllers()

    def UnityInitializationReadyMessageReceived(self):
        self.unityInitializationReadyMessageReceived = True

    def UnityEnvironmentStartedMessageReceived(self):
        self.unityEnvironmentStartedMessageReceived = True

    def UnityEnvironmentStoppedMessageReceived(self):
        self.unityEnvironmentStoppedMessageReceived = True
        
    def InitializeUnityCommunicationController(self):
        self.unityCommunicationController = UnityCommunicationController()
        self.unityCommunicationController.SetUnityInitializationReadyMessageCallback(self.UnityInitializationReadyMessageReceived)
        self.unityCommunicationController.SetUnityEnvironmentStartedMessageCallback(self.UnityEnvironmentStartedMessageReceived)
        self.unityCommunicationController.SetUnityEnvironmentStoppedMessageCallback(self.UnityEnvironmentStoppedMessageReceived)

    def InitializeControllers(self):
        self.InitializeUnityCommunicationController()

    def StartUnityProcess(self):
        pass

    def StopUnityProcess(self):
        pass

    def Update(self):
        if not self.unityInitializationReadyMessageReceived:
            return
        pass

    def Terminate(self):
        pass


if __name__ == "__main__":
    avciMaster = AvciMaster()
    
    avciMaster.StartUnityProcess()

    while True:
        avciMaster.Update()
