
import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

try:
    from api.v1.patents import router
    print("Import successful")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
