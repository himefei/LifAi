import winreg
import sys
import os

def setup_context_menu():
    try:
        # Register context menu in Windows registry
        key_path = r"Software\Classes\*\shell\ImproveText"
        
        # Create main key
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                            winreg.KEY_WRITE)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Improve Text with AI")
        winreg.CloseKey(key)
        
        # Create command key
        command_key_path = f"{key_path}\\command"
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key_path)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, command_key_path, 0,
                            winreg.KEY_WRITE)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, 
                        f'"{sys.executable}" "{os.path.abspath(__file__)}" "%1"')
        winreg.CloseKey(key)
        
    except Exception as e:
        print(f"Error setting up context menu: {e}")
