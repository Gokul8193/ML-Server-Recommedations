import subprocess
import sys
import os
import argparse

parser = argparse.ArgumentParser(description="Run all scripts.")
parser.add_argument("-d", "--days", type=int, default=365, help="Number of days for Fetch_params.py")
args = parser.parse_args()

scripts = [
    {"name": "Fetch_params.py", "args": ["-c", "1634725968", "-l", "4448717117"]},
    {"name": "Merging.py", "args": []},
    {"name": "recom7_2.py", "args": []},
    {"name": "Saving_recom.py", "args": []}
]
folder = os.path.dirname(os.path.abspath(__file__))

for script in scripts:
    script_path = os.path.join(folder, script["name"])
    run_args = script["args"][:]
    if script["name"] == "Fetch_params.py" and args.days is not None:
        run_args += ["-d", str(args.days)]
    print(f"Running {script_path}...")
    result = subprocess.run([sys.executable, script_path] + run_args, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)