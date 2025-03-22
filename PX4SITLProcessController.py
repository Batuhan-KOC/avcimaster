import subprocess
import threading
import os
from enum import Enum

from SharedData import SharedData

class PX4SITLProcessController:
    class State(Enum):
        IDLE = 0
        INITIALIZING = 1
        STARTED = 2
        STOPPED = 3

    def __init__(self):
        self.state = SharedData(self.State.IDLE)
        self._avciPilotDirectory = "../avcipilot"

    def StartSITL(self):
        self._StartPX4Simulation()

    def StopSITL(self):
        self._StopPX4Simulation()

    def GetState(self)->State:
        return self.state.Get()

    def SetProcessErrorCallback(self, processErrorCallback):
        pass

    def _StartPX4Simulation(self):
        pass

    def _StopPX4Simulation(self):
        pass

    def _RunPX4Simulation(self):
        pass