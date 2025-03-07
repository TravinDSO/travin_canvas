"""
Travin Canvas Application Launcher

This script provides a convenient way to start the Travin Canvas application
using the Streamlit CLI. It handles locating the main application file,
launching the Streamlit server, and managing any errors that occur during startup.

Key features:
- Simple one-command application startup
- Path resolution for finding the main.py file
- Error handling for common startup issues
- Clean shutdown on keyboard interrupt

Usage:
    python run.py

Dependencies:
- subprocess: For running the Streamlit CLI
- os: For file path operations
- sys: For exit code management
"""

import os
import subprocess
import sys
import time

def main():
    """
    Run the Travin Canvas application.
    
    This function locates the main.py file, verifies its existence,
    and launches the Streamlit server to run the application.
    It handles errors gracefully and provides appropriate feedback
    to the user in case of failures.
    
    Exit codes:
    - 0: Successful execution or clean shutdown
    - 1: Error (file not found, Streamlit error, or unexpected exception)
    """
    # Get the absolute path to the main.py file
    main_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "main.py")
    
    # Check if the file exists
    if not os.path.exists(main_py_path):
        print(f"Error: Could not find {main_py_path}")
        sys.exit(1)
    
    # Run the Streamlit application
    print("Starting Travin Canvas...")
    try:
        subprocess.run(["streamlit", "run", main_py_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        # Print consistent shutdown messages
        print("\nStopping...")
        # Brief pause to mimic the UI delay
        time.sleep(1)
        print("Travin Canvas stopped.")
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 