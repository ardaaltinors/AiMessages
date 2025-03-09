import subprocess

def send_imessage(phone_number, message, debug=False):
    script = f'''
    tell application "Messages"
        send "{message}" to buddy "{phone_number}"
    end tell
    '''
    if debug:
        print("messageToSend: ", message)
    else:
        subprocess.run(["osascript", "-e", script])


if __name__ == "__main__":
    # Example
    phone_number = "+905555555555"
    message = "selam"
    send_imessage(phone_number, message)