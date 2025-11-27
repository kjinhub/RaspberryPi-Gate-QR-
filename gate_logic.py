# gate_logic.py

import requests
import jwt
import time
import RPi.GPIO as GPIO 
# Import configuration settings. SERVER_PUBLIC_KEY is NOT used here anymore.
from config import GATE_VERIFY_API_URL, GATE_ID


# --- A. GPIO and UX Functions (PWM Servo Control) ---

# --- GPIO Pin Configuration ---
# BCM 17 pin is set for the PWM signal to control the servo motor
PWM_PIN = 17 
GATE_OPEN_ANGLE = 7.5  # PWM Duty Cycle for 90 degrees (Open position)
GATE_CLOSE_ANGLE = 2.5 # PWM Duty Cycle for 0 degrees (Closed position)
GATE_FREQ = 50         # PWM Frequency for servo motors (50 Hz)
GATE_OPEN_TIME = 3     # Time the gate remains open (seconds)

# Helper function to convert angle (0-180) to Duty Cycle (2.5-12.5)
# This function is assumed to be defined above if needed elsewhere, 
# but the current code uses fixed Duty Cycles (7.5 and 2.5).

def open_gate():
    """Controls the servo motor via PWM to open and close the gate."""
    
    # Setup GPIO (using BCM mode)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PWM_PIN, GPIO.OUT)
    
    # Create a PWM instance
    pwm = GPIO.PWM(PWM_PIN, GATE_FREQ)
    
    try:
        print("Starting PWM for servo control...")
        
        # 1. Ensure motor starts at the closed position (0 degrees)
        pwm.start(GATE_CLOSE_ANGLE)
        time.sleep(0.5) 

        # 2. Gate OPEN: Move motor to open position 
        pwm.ChangeDutyCycle(GATE_OPEN_ANGLE) 
        print(f"🚦 PWM Signal Change: BCM {PWM_PIN} to {GATE_OPEN_ANGLE} DC. Gate OPEN")
        
        # 3. Wait while the gate is open
        time.sleep(GATE_OPEN_TIME)                     
        
        # 4. Gate CLOSE: Return motor to closed position
        pwm.ChangeDutyCycle(GATE_CLOSE_ANGLE)  
        print(f"🚪 PWM Signal Change: BCM {PWM_PIN} to {GATE_CLOSE_ANGLE} DC. Gate CLOSE")
        time.sleep(0.5) 

    except Exception as e:
        print(f"🚨 PWM Control Error Occurred: {e}")
        
    finally:
        # Stop PWM and clean up GPIO settings
        pwm.stop()
        GPIO.cleanup() 
        print("PWM stopped and GPIO cleaned up.")


def display_status(is_success, reason=""):
    """Simulates the trust UX (Green/Red light) based on server response."""
    if is_success:
        print("✅ Green Light ON: Payment completed. Please proceed!")
    else:
        print(f"❌ Red Light ON: Access denied. Reason: {reason}")


# --- B. Core Logic Function (Simplified for Prototype) ---

def verify_consume_token(token_string: str, gate_id: str = GATE_ID) -> dict:
    """
    Prototype Logic: Skips local signature check and immediately asks the backend server
    to verify payment status and consume the token.
    """
    print(f"\n--- Token Verification Started (Gate ID: {gate_id}) ---")

    # 1. Attempt to Parse Token Payload (To extract device info before sending to server)
    try:
        # We must disable signature verification as the public key is not used in this prototype.
        payload = jwt.decode(
            token_string, 
            options={"verify_signature": False}
        )
    except Exception as e:
        reason = f"TOKEN_PARSING_ERROR: {e.__class__.__name__}"
        print(f"🚨 Local Parsing Failed: Token format error. Denied. Reason: {reason}")
        display_status(False, reason)
        return {"status": "BLOCK", "reason": reason}
        
    # 2. Call Server verify-consume API (Zero-Trust Core)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GATE_API_KEY}" # Gate authentication
    }
    api_payload = {
        "token": token_string, # Send the full token string to the server
        "gate_id": gate_id,
        "device_hash": payload.get('device_hash', 'UNKNOWN'), # Extracted device binding info
    }

    try:
        print(f"🌐 Requesting Final Verification/Consume from Server: {GATE_VERIFY_API_URL}")
        response = requests.post(GATE_VERIFY_API_URL, json=api_payload, headers=headers, timeout=0.4) 

        # 3. Check Server Response (The gate MUST ONLY open on Server 'OK')
        if response.status_code == 200:
            server_result = response.json()
            if server_result.get("status") == "OK":
                display_status(True)
                open_gate() # Open gate ONLY when server gives OK
                return {"status": "OPEN", "reason": "Server OK"}
            else:
                reason = server_result.get("reason", "Server Denied")
                display_status(False, reason) 
                return {"status": "BLOCK", "reason": reason}

        else:
            print(f"🌐 Server Communication Error: HTTP {response.status_code}")
            display_status(False, "SERVER_COMMUNICATION_ERROR")
            return {"status": "BLOCK", "reason": "SERVER_COMMUNICATION_ERROR"}
    
    except requests.exceptions.Timeout:
        reason = "TIMEOUT"
        print("🌐 Server Communication Error: Timeout occurred (Security First, Default Block)")
        display_status(False, reason)
        return {"status": "BLOCK", "reason": reason}
    except requests.exceptions.RequestException as e:
        reason = f"NETWORK_FAIL: {e.__class__.__name__}"
        print(f"🌐 Server Communication Error: Network access failed. Denied. Reason: {reason}")
        return {"status": "BLOCK", "reason": reason}