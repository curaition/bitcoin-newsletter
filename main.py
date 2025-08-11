#!/usr/bin/env python3
"""
Main entry point for the crypto newsletter application.
This file is designed to be detected by Railpack for automatic deployment.
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    # Import and run the process manager
    from start_processes import ProcessManager
    
    manager = ProcessManager()
    sys.exit(manager.run())
