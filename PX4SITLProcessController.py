import subprocess
import threading
import os
import time
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
        self._sitlThread = None
        self._sitlProcess = None
        self._sitlRunning = False
        self._sitlTerminate = False
        self._mavlinkThread = None
        self._mavlinkRunning = False
        self._takeOffCommandSendToSitl = False

    def StartSITL(self):
        if not self._sitlRunning:
            self._StartPX4Simulation()

    def StopSITL(self):
        if self._sitlRunning:
            self._StopPX4Simulation()

    def GetState(self)->State:
        return self.state.Get()

    def SetProcessErrorCallback(self, processErrorCallback):
        pass

    def _StartPX4Simulation(self):
        self._sitlTerminate = False
        self._sitlThread = threading.Thread(target=self._RunPX4Simulation, daemon=True)
        self._mavlinkThread = threading.Thread(target=self._RunMavlink, daemon=True)
        self._sitlThread.start()
        self._mavlinkThread.start()

    def _StopPX4Simulation(self):
        self._sitlTerminate = True

        self._sitlThread.join()
        self._mavlinkThread.join()

    def _RunPX4Simulation(self):
        self._sitlRunning = True

        self._takeOffCommandSendToSitl = False
        
        processStartedWithoutError = False

        try:
            self._CreateSitlProcess()
            processStartedWithoutError = True
        except Exception as e:
            self._sitlTerminate = True

        while not self._sitlTerminate:
            if not self._takeOffCommandSendToSitl:
                takeoffReady = self._IsSitlReadyToTakeoff()
                if takeoffReady:
                    self._InitializeAndTakeOff()
                    self._takeOffCommandSendToSitl = True
            else:
                # Do not busy wait
                time.sleep(0.1)

        if processStartedWithoutError:
            self._sitlProcess.terminate()
            self._sitlProcess.wait()

        self._sitlRunning = False

    def _RunMavlink(self):
        self._mavlinkRunning = True

        # Wait until takeoff command
        while not self._takeOffCommandSendToSitl and not self._sitlTerminate:
            pass

        if not self._sitlTerminate:
            # TODO: initialize mavlink here
            pass

        self._mavlinkRunning = False

    def _SendCommandToSitlProcess(self, command):
        try:
            self._sitlProcess.stdin.write(command + "\n")
            self._sitlProcess.stdin.flush()
        except Exception as e:
            print(f"Error sending command: {e}")

    def _CreateSitlProcess(self):
        sitlProcessCommand = "HEADLESS=1 make px4_sitl gazebo-classic"
        sitlProcessDirectory = "../avcipilot"

        systemEnvironment = os.environ.copy()
        sitlEnvironment = systemEnvironment
        sitlEnvironment["PX4_HOME_LAT"] = "1.0"
        sitlEnvironment["PX4_HOME_LON"] = "1.0"
        sitlEnvironment["PX4_HOME_ALT"] = "0.0"

        self._sitlProcess = subprocess.Popen(
                        sitlProcessCommand,
                        cwd=sitlProcessDirectory,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,  # Allow sending input
                        shell=True,
                        text=True,  # Capture output as text
                        env=sitlEnvironment
                    )
    
    def _IsSitlReadyToTakeoff(self):
        for line in self._sitlProcess.stdout:
            if line.__contains__("Ready for takeoff!"):
                return True
        return False
    
    def _InitializeAndTakeOff(self):
        self._SendCommandToSitlProcess("param set MPC_TKO_SPEED 5")
        self._SendCommandToSitlProcess("param set MIS_TAKEOFF_ALT 50")
        self._SendCommandToSitlProcess("commander takeoff")