# Works!!!

import time
import tinytuya

# ----------------------------------------------------
# CONFIGURATION - Replace with your information
# ----------------------------------------------------
DEVICE_ID = "eb6f9bf3a0d35477e5jpua"
IP_ADDRESS = "192.168.0.103"
LOCAL_KEY = "BgPx)~6PD/BG7hIw"

# Initialize connection
# The SP10 uses Tuya protocol 3.3 (or occasionally 3.1)
plug = tinytuya.OutletDevice(DEVICE_ID, IP_ADDRESS, LOCAL_KEY)
plug.set_version(3.3) 


# ----------------------------------------------------
# CONTROL FUNCTIONS
# ----------------------------------------------------
def get_plug_status():
    """Fetches and prints the current state of the plug."""
    # update=True forces the library to poll the plug live
    status = plug.status() 
    
    if "dps" in status:
        # Index '1' represents the main power switch state (True=On, False=Off)
        is_on = status["dps"].get("1")
        print(f"🔌 Plug is currently: {'ON' if is_on else 'OFF'}")
        return is_on
    else:
        print("❌ Error communicating with the plug. Check your IP/Key.")
        print("Response received:", status)
        return None

def turn_on():
    """Turns the plug on."""
    print("▶️ Sending ON command...")
    plug.turn_on()

def turn_off():
    """Turns the plug off."""
    print("⏹️ Sending OFF command...")
    plug.turn_off()


# ----------------------------------------------------
# EXAMPLE EXECUTION RUN
# ----------------------------------------------------
if __name__ == "__main__":
    # 1. Check current status
    get_plug_status()
    time.sleep(1)
    
    # 2. Turn it on
    turn_on()
    time.sleep(2)
    
    # 3. Double check status changed
    get_plug_status()
    time.sleep(2)
    
    # 4. Turn it off
    turn_off()