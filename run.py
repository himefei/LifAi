import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

from lifai.core.app_hub import LifAiHub

if __name__ == "__main__":
    app = LifAiHub()
    app.run() 