import os
import sys
import shutil

def add_to_startup():
    startup_path = os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
    shortcut_name = "Internet Carbon Tracker.lnk"
    target_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "co2_tracker.exe")
    
    # Check if the executable exists
    if os.path.exists(target_path):
        # Create a shortcut
        import winshell
        winshell.shortcut(
            target=target_path,
            shortcut=shortcut_name,
            description='Launch Internet Carbon Tracker at startup.'
        )

if __name__ == "__main__":
    add_to_startup()
