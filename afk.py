import time
import pyautogui

def simulate_activity():
    """
    Simulate activity by pressing and releasing the Shift key.
    """
    pyautogui.press('shift')
    print("Shift key pressed on ", time.strftime("%Y-%m-%d %H:%M:%S"))

def main():
    print("Anti-AFK script is running. Press Ctrl+C to stop.")
    try:
        while True:
            simulate_activity()
            # Wait for 3 minutes (180 seconds) before simulating activity again
            time.sleep(180)
    except KeyboardInterrupt:
        print("Script terminated by user.")

if __name__ == "__main__":
    main()
