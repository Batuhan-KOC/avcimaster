from pymavlink import mavutil
import time
import subprocess
import threading
import os

from sitlWorker import SITLWorker

if __name__ == "__main__":
    sitl_worker = SITLWorker()
    sitl_worker.start_sitl()

    try:
        while True:
            if sitl_worker.takeOffRequested:
                master = mavutil.mavlink_connection('udp:localhost:14540')

                master.wait_heartbeat()
                while True:
                    msg = master.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
                    if msg:
                        alt = msg.alt / 1e3
                        print(f"Alt: {alt}")
                        if(alt > 49):
                            master.close()
                            sitl_worker.takeOffRequested = False
                            break

            time.sleep(1)  # Prevent CPU overuse
    except KeyboardInterrupt:
        print("Stopping SITL...")
        sitl_worker.stop_sitl()