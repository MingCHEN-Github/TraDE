import subprocess

def run_load_scripts():
    # Define the paths to each load script
    scripts = [
        "/home/ubuntu/ms_scheduling/social_net/strategy/comparisions/workload1_composePost/load1.py",
        "/home/ubuntu/ms_scheduling/social_net/strategy/comparisions/workload2_readUserTimeline/load2.py",
        "/home/ubuntu/ms_scheduling/social_net/strategy/comparisions/workload3_readHomeTimeline/load3.py",
        "/home/ubuntu/ms_scheduling/social_net/strategy/comparisions/workload4_mixWrokload/load4.py"
    ]

    for script in scripts:
        print(f"Running {script}...")
        try:
            # Run the script using Python interpreter
            result = subprocess.run(["python3", script], check=True, capture_output=True, text=True)
            print(f"Output of {script}:\n{result.stdout}")
            if result.stderr:
                print(f"Error in {script}:\n{result.stderr}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to run {script}:\n{e.stderr}")
        except FileNotFoundError:
            print(f"Script {script} not found.")
        except Exception as e:
            print(f"An error occurred while running {script}: {e}")

# Run the load scripts in turns
run_load_scripts()
