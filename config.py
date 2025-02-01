import os
import winreg as reg

class AnsiColor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def set_cmd_title(title):
    os.system(f'title {title}')

def set_virtual_terminal_level():
    try:
        # Open the Console key in the HKEY_CURRENT_USER hive
        key = reg.OpenKey(reg.HKEY_CURRENT_USER, r'Console', 0, reg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        # If the key doesn't exist, create it
        key = reg.CreateKey(reg.HKEY_CURRENT_USER, r'Console')

    try:
        # Set the VirtualTerminalLevel value to 1
        reg.SetValueEx(key, 'VirtualTerminalLevel', 0, reg.REG_DWORD, 1)
        print("Registry modification completed.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        reg.CloseKey(key)

if __name__ == "__main__":
    set_virtual_terminal_level()
