import os
import time

print("Script is running and will execute run_all.py every day at 17:20.")

# Infinite loop to keep the script running
while True:
    # Get the current time
    current_time = time.strftime("%H:%M")
    
    # Check if the current time is 17:20    
    if current_time == "17:20":
        print("Running script: /home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params_minori/SCheduled/run_all.py")
            
        # Execute the run_all.py script
        os.system('python "/home/minorilabs/Desktop/Google ads Client/google-ads-python/examples/reporting/input_params_minori/SCheduled/run_all.py"')
        
        # Wait for 60 seconds to avoid multiple executions within the same minute
        print("Execution completed. Waiting for the next scheduled time...")
        time.sleep(60)
    else:
        # Sleep for 1 second before checking the time again
        time.sleep(1)