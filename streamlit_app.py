"""
Streamlit Community Cloud Root Entrypoint
Delegates directly to app.py
"""
import runpy
import sys
import os

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Run app.py
runpy.run_path(os.path.join(os.path.dirname(__file__), "app.py"), run_name="__main__")
