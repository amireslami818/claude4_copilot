import json
import os
from datetime import datetime

# Sample data to be written to JSON
data = {
    "step": "Step 1",
    "status": "In Progress",
    "timestamp": datetime.now().isoformat()
}

# Ensure the step1 directory exists
os.makedirs("step1", exist_ok=True)

# Write the data to a JSON file in the step1 directory
with open("step1/step1.json", "w") as f:
    json.dump(data, f, indent=4)

print("Data written to step1/step1.json")