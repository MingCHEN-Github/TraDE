import os
import subprocess

# Define the parameters
thread_num = 4
connections = 100

duration = '2m'
QPS = [200, 500, 1000]


script_path = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/read-home-timeline.lua"
url = [
    # deployed with k8s-Burstable method
    "http://nginx-thrift.social-network.svc.cluster.local:8080/wrk2-api/home-timeline/read",
    # # deployed with NetMARKS method
    "http://nginx-thrift.social-network2.svc.cluster.local:8080/wrk2-api/home-timeline/read",
    # deployed with TraDE method
    "http://nginx-thrift.social-network3.svc.cluster.local:8080/wrk2-api/home-timeline/read"
]

# Define the output file path in the current directory
output_file = os.path.join(os.getcwd(), "/home/ubuntu/ms_scheduling/social_net/strategy/comparisions/workload2_readUserTimeline/output_result2.txt")

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
