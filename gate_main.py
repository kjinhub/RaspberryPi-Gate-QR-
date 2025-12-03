# gate_main.py

import sys
import os
import time
# Imports the core verification logic
from gate_logic import verify_consume_token

def main_loop():
    print("------------------------------------------")
    print(f"🚀 Scan&Go Gate Controller ({os.uname().nodename}) Started")
    print(f"Listening for QR/Barcode input on stdin...")
    print("------------------------------------------")
    
    # Since the QR scanner acts like a USB keyboard, it sends data via standard input.
    while True:
        try:
            # The token string will be automatically entered when a QR code is scanned.
            token_string = input("QR Token Scan Waiting: ")
            
            if not token_string:
                continue
                
            print(f"\n[SCAN] Token Received: {token_string[:10]}...")
            
            # Pass the received token to the verification logic
            result = verify_consume_token(token_string.strip())
            
            print(f"[RESULT] Status: {result.get('status')}, Reason: {result.get('reason')}")
            
        except EOFError:
            print("Input stream ended. Program terminated.")
            break
        except KeyboardInterrupt:
            print("\nProgram forced termination.")
            break
        except Exception as e:
            print(f"General error occurred: {e}")

if __name__ == "__main__":
    try:
        main_loop()
    finally:
        print("Gate Controller Shutdown.")