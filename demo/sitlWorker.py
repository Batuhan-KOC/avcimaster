# sitlworker.py
import subprocess
import threading
import os

class SITLWorker:
    def __init__(self):
        self.sitlrunning = False  # Boolean flag to track SITL status
        self.process = None  # Store process reference
        self.thread = None  # Store thread reference
        self.terminateRequested = False
        self.takeOffRequested = False
        self.sitl_directory = "../avcipilot"

    def start_sitl(self):
        """Start PX4 SITL in a separate thread"""
        if self.sitlrunning:
            print("SITL is already running.")
            return
        self.terminateRequested = False
        self.takeOffRequested = False
        self.thread = threading.Thread(target=self._run_sitl, daemon=True)
        self.thread.start()

    def _send_command(self, command):
        """Send a command to the running PX4 SITL process"""
        if self.sitlrunning and self.process:
            try:
                self.process.stdin.write(command + "\n")
                self.process.stdin.flush()
                print(f"Sent command: {command}")
            except Exception as e:
                print(f"Error sending command: {e}")
        else:
            print("SITL is not running.")

    def _run_sitl(self):
        """Runs the SITL process and captures output"""
        sitl_command = "HEADLESS=1 make px4_sitl gazebo-classic"

        # Set environment variables before starting SITL
        env = os.environ.copy()  # Copy current environment variables
        env["PX4_HOME_LAT"] = "1.0"
        env["PX4_HOME_LON"] = "1.0"
        env["PX4_HOME_ALT"] = "0.0"

        try:
            # Start the process inside the specified directory
            self.process = subprocess.Popen(
                sitl_command,
                cwd=self.sitl_directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,  # Allow sending input
                shell=True,
                text=True,  # Capture output as text
                env=env
            )

            self.sitlrunning = True
            print("SITL started.")

            # Read process output in real-time
            while not self.terminateRequested:
                for line in self.process.stdout:
                    print(line, end="")  # Print output to console
                    if line.__contains__("Ready for takeoff!"):
                        self._send_command("param set MPC_TKO_SPEED 5")
                        self._send_command("param set MIS_TAKEOFF_ALT 50")
                        self._send_command("commander takeoff")
                        self.takeOffRequested = True

            self.process.wait()  # Wait for the process to finish
        except Exception as e:
            print(f"Error starting SITL: {e}")
            self.sitl_directory="avcipilot"
            self._run_sitl()
        finally:
            self.sitlrunning = False
            print("SITL stopped.")

    def stop_sitl(self):
        """Stops the SITL process if running"""
        if self.sitlrunning and self.process:
            self.terminateRequested = True
            self.process.terminate()  # Try to terminate gracefully
            self.process.wait()
            self.sitlrunning = False
            print("SITL terminated.")
