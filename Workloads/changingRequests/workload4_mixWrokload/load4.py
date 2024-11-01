import os
import subprocess

# Define the parameters
thread_num = 4
connections = 100

# requests_ratios = [[0.6, 0.2, 0.2], [0.2, 0.6, 0.2], [0.2, 0.2, 0.6]]


duration = '2m'
QPS = [200, 500, 1000]
# QPS = [300, 600]

# run mix workload
script_path = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/mixed-workload.lua"

# order 1: 
url = [
    "http://nginx-thrift.social-network.svc.cluster.local:8080",
    "http://nginx-thrift.social-network2.svc.cluster.local:8080",
   "http://nginx-thrift.social-network3.svc.cluster.local:8080"
]

# Define the output file path in the current directory
output_file = os.path.join(os.getcwd(), "output_result4_v1.txt")

# Ensure the output file is empty at the start
with open(output_file, 'w') as f:
    f.write("")

# Iterate over the QPS and URLs to run the commands
for qps in QPS:
    for i in range(len(url)):
        command = [
            "/home/ubuntu/DeathStarBench/wrk2/wrk",
            "-D", "exp",
            f"-t{thread_num}",
            f"-c{connections}",
            f"-d{duration}",
            "-L",
            "-s", script_path,
            url[i],
            f"-R{qps}"
        ]
        print(f"Running command: {' '.join(command)}")
        
        with open(output_file, 'a') as f:
            process = subprocess.Popen(command, stdout=f, stderr=subprocess.STDOUT)
            process.wait()
        
        print("Done for this command")
