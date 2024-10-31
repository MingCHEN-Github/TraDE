'''test for different 3 different commands in the same namesapce'''


# compos-post request
url_1 = "http://nginx-thrift.social-network2.svc.cluster.local:8080/wrk2-api/post/compose"
script_path_1 = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/compose-post.lua"  

# read home time line request
url_2 = "http://nginx-thrift.social-network2.svc.cluster.local:8080/wrk2-api/home-timeline/read"
script_path_2 = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/read-home-timeline.lua"

# read user timeline request
url_3 = "http://nginx-thrift.social-network2.svc.cluster.local:8080/wrk2-api/user-timeline/read"
script_path_3 = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/read-user-timeline.lua"


# run mix workload
url4 = "http://nginx-thrift.social-network2.svc.cluster.local:8080"
script_path4 = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/mixed-workload.lua"

urls = [url_1, url_2, url_3]
script_paths = [script_path_1, script_path_2, script_path_3]

'''load test for homtimeline request'''
import os
from time import sleep

for i in range(len(urls)):
    # QPS = [300, 500]
    # durations = ['1', '5', '10']

    QPS = [100, 500, 1000]
    durations = ['3']

    # using the above urls and script path, run the load test.
    # the example command running at terminal is:
    # ubuntu@k8s-master:~/DeathStarBench/socialNetwork$ ../wrk2/wrk -D exp -t2 -c100 -d2m -L -s ./wrk2/scripts/social-network/read-home-timeline.lua  http://nginx-thrift.social-network2.svc.cluster.local:8080/wrk2-api/home-timeline/read -R200
    for qps in QPS:
        for duration in durations:
            command = f"/home/ubuntu/DeathStarBench/wrk2/wrk -D exp -t2 -c100 -d{duration}m -L -s {script_paths[i]} {urls[i]} -R{qps}"
            print(f"Running command: {command}")
            os.system(command)
            # sleep(int(duration) * 60 + 10)
            print("Done for this command")



















# '''load test for homtimeline request'''
# import os
# from time import sleep

# # path to the lua script for the home-timeline request
# script_path = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/read-home-timeline.lua"

# # urls for the home-timeline request
# url_1 = "http://nginx-thrift.social-network.svc.cluster.local:8080/wrk2-api/home-timeline/read"
# url_2 = "http://nginx-thrift.social-network2.svc.cluster.local:8080/wrk2-api/home-timeline/read"
# url_3 = "http://nginx-thrift.social-network3.svc.cluster.local:8080/wrk2-api/home-timeline/read"


# # QPS = [300, 500]
# # durations = ['1', '5', '10']

# QPS = [200, 500, 1000]
# durations = ['3']


# # using the above urls and script path, run the load test.
# # the example command running at terminal is:
# # ubuntu@k8s-master:~/DeathStarBench/socialNetwork$ ../wrk2/wrk -D exp -t2 -c100 -d2m -L -s ./wrk2/scripts/social-network/read-home-timeline.lua  http://nginx-thrift.social-network2.svc.cluster.local:8080/wrk2-api/home-timeline/read -R200
# for qps in QPS:
#     for duration in durations:
#         command_1 = f"/home/ubuntu/DeathStarBench/wrk2/wrk -D exp -t2 -c100 -d{duration}m -L -s {script_path} {url_1} -R{qps}"
#         command_2 = f"/home/ubuntu/DeathStarBench/wrk2/wrk -D exp -t2 -c50 -d{duration}m -L -s {script_path} {url_2} -R{qps}"
#         command_3 = f"/home/ubuntu/DeathStarBench/wrk2/wrk -D exp -t2 -c50 -d{duration}m -L -s {script_path} {url_3} -R{qps}"
#         print(f"Running command1: {command_1}")
#         os.system(command_1)
#         sleep(int(duration) * 60 + 10)
        
        
#         print(f"Running command2: {command_2}")
#         os.system(command_2)
#         sleep(int(duration) * 60 + 10)
        
#         print(f"Running command3: {command_3}")
#         os.system(command_3)
#         sleep(int(duration) * 60 + 10)
        
#         print("Done")