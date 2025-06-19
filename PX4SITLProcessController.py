import subprocess
import threading
import socket
import struct
import os
import time
import logging
from enum import Enum
from pymavlink import mavutil

from SharedData import SharedData

logging.basicConfig(level=logging.INFO)

class PX4SITLProcessController:
    """
    Controls the PX4 SITL process and handles MAVLink communication.
    """
    class State(Enum):
        IDLE = 0
        START_REQUESTED = 1
        INITIALIZING_SITL_PROCESS = 2
        INITIALIZING_MAVLINK = 3
        STARTED = 4
        STOPPED = 5

    def __init__(self):
        """Initialize controller state and threads."""
        self.state = SharedData(self.State.IDLE)
        self._sitlThread = None
        self._sitlProcess = None
        self._sitlRunning = False
        self._initializationCompleted = False
        self._sitlTerminate = False
        self._mavlinkThread = None
        self._mavlinkRunning = False
        self._takeOffCommandSendToSitl = False
        self._processErrorCallback = None
        self._Socket10004 = None
        
    def Terminate(self):
        self._sitlTerminate = True
        self._sitlThread.join()
        self._mavlinkThread.join()
        self._Socket10004.close()

    def StartSITL(self):
        if not self._sitlRunning:
            print("Starting PX4 SITL simulation")
            self._StartPX4Simulation()

    def StopSITL(self):
        if self._sitlRunning:
            self._StopPX4Simulation()

    def GetState(self)->State:
        return self.state.Get()
    
    def SetState(self, value):
        return self.state.Set(value)

    def SetProcessErrorCallback(self, processErrorCallback):
        self._processErrorCallback = processErrorCallback

    def _StartPX4Simulation(self):
        self._sitlRunning = True
        self._sitlTerminate = False
        self._initializationCompleted = False
        self.SetState(self.State.START_REQUESTED)
        self._sitlThread = threading.Thread(target=self._RunPX4Simulation, daemon=True)
        self._mavlinkThread = threading.Thread(target=self._RunMavlink, daemon=True)
        self._sitlThread.start()
        self._mavlinkThread.start()

    def _StopPX4Simulation(self):
        self._sitlTerminate = True

        self._sitlThread.join()
        self._mavlinkThread.join()
        
        self._sitlThread = None
        self._mavlinkThread = None
        
        self.SetState(self.State.STOPPED)

    def _RunPX4Simulation(self):
        self._takeOffCommandSendToSitl = False
        
        processStartedWithoutError = self._TryToCreateSitlProcess()
            
        print("SITL process created successfully." if processStartedWithoutError else "Failed to create SITL process.")
        if processStartedWithoutError:
            self._SitlProcessRunControl()

        while not self._sitlTerminate:
            if not self._takeOffCommandSendToSitl:
                self.SetState(self.State.INITIALIZING_SITL_PROCESS)
                self._SitlPreTakeoffInitialization()
            else:
                sitlProcessRunning = self._SitlProcessRunControl()
                if not sitlProcessRunning:
                    break
                time.sleep(0.1)

        if processStartedWithoutError and sitlProcessRunning:
            self._SitlProcessTerminateAndWait()

        self._sitlRunning = False
        
    def _Initialize10004TransmitSocket(self):
        self._Socket10004 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
    def _SendMessageFrom10004TransmitSocket(self, lat, lon, alt, roll, pitch, yaw):
        data = struct.pack("!6f", lat, lon, alt, roll, pitch, yaw)
        self._Socket10004.sendto(data, ("127.0.0.1", 10004))

    def _RunMavlink(self):
        self._mavlinkRunning = True

        # Wait until takeoff command
        print("Waiting for takeoff command to be sent to SITL to start mavlink.")
        while not self._takeOffCommandSendToSitl and not self._sitlTerminate:
            time.sleep(0.1)

        mavlinkConnection = None

        self.SetState(self.State.INITIALIZING_MAVLINK)

        if not self._sitlTerminate:
            print("Creating MAVLink connection.")
            while True:
                try:
                    mavlinkConnection = mavutil.mavlink_connection('udp:localhost:14540')
                    break
                except Exception:
                    pass
            
            print("Waiting for MAVLink heartbeat.")
            while True:
                try:
                    mavlinkConnection.wait_heartbeat()
                    break
                except:
                    pass

        print("MAVLink connection established.")

        self._Initialize10004TransmitSocket()
                     
        lat = 0
        lon = 0
        alt = 0
        roll = 0
        pitch = 0
        yaw = 0
        while not self._sitlTerminate:
            msg = mavlinkConnection.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
            if msg:
                lat = msg.lat / 1e7
                lon = msg.lon / 1e7
                alt = msg.alt / 1e3
                
            msg = mavlinkConnection.recv_match(type='ATTITUDE', blocking=True)
            if msg:
                roll = msg.roll * (180 / 3.14159)
                pitch = msg.pitch * (180 / 3.14159)
                yaw = msg.yaw * (180 / 3.14159)
                
            if not self._initializationCompleted:
                self._CheckInitializationByAltitude(alt)
            else:
                self._SendMessageFrom10004TransmitSocket(lat, lon, alt, roll, pitch, yaw)

        mavlinkConnection.close()
        
        self._mavlinkRunning = False

    def _CreateSitlProcess(self):
        """Creates the SITL process with the appropriate environment."""
        sitlProcessCommand = "HEADLESS=1 make px4_sitl gazebo-classic"
        sitlProcessDirectory = os.path.join("..", "avcipilot")

        systemEnvironment = os.environ.copy()
        sitlEnvironment = systemEnvironment
        sitlEnvironment["PX4_HOME_LAT"] = "1.0"
        sitlEnvironment["PX4_HOME_LON"] = "1.0"
        sitlEnvironment["PX4_HOME_ALT"] = "0.0"

        print(f"Creating SITL process with command: {sitlProcessCommand}")
        self._sitlProcess = subprocess.Popen(
                        sitlProcessCommand,
                        cwd=sitlProcessDirectory,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,
                        shell=True,
                        text=True,
                        env=sitlEnvironment
                    )

    def _SendCommandToSitlProcess(self, command):
        """Sends a command to the SITL process."""
        try:
            self._sitlProcess.stdin.write(command + "\n")
            self._sitlProcess.stdin.flush()
        except Exception as e:
            logging.error(f"Error sending command: {e}")

    def _IsSitlReadyToTakeoff(self):
        for line in self._sitlProcess.stdout:
            if line.__contains__("Ready for takeoff!"):
                return True
        return False
    
    def _IsSitlProcessRunning(self):
        exitCode = self._sitlProcess.poll()
        if exitCode is not None:
            return False
        return True
    
    def _SitlProcessRunControl(self):
        sitlProcessRunning = self._IsSitlProcessRunning()
        if not sitlProcessRunning:
            self._processErrorCallback()
            self._sitlTerminate = True
        return sitlProcessRunning
    
    def _InitializeAndTakeOff(self):
        self._SendCommandToSitlProcess("param set MPC_TKO_SPEED 5")
        self._SendCommandToSitlProcess("param set MIS_TAKEOFF_ALT 50")
        self._SendCommandToSitlProcess("commander takeoff")
        
    def _SitlPreTakeoffInitialization(self):
        takeoffReady = self._IsSitlReadyToTakeoff()
        if takeoffReady:
            print("SITL is ready for takeoff.")
            self._InitializeAndTakeOff()
            print("Takeoff command sent to SITL.")
            self._takeOffCommandSendToSitl = True
            
    def _SitlProcessTerminateAndWait(self):
        self._sitlProcess.terminate()
        self._sitlProcess.wait()
        
    def _TryToCreateSitlProcess(self):
        try:
            self._CreateSitlProcess()
            return True
        except Exception as e:
            print(f"Error creating SITL process: {e}")
            self._sitlTerminate = True
            return False
        
    def _CheckInitializationByAltitude(self, alt):
        if alt > 48.0:
            self._initializationCompleted = True
            self.SetState(self.State.STARTED)
            print("SITL initialization completed successfully.")
        else:
            print(f"Current altitude: {alt} m")
            print('\033[F\033[K', end='')