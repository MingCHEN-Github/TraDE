from prometheus_api_client import PrometheusConnect, MetricRangeDataFrame
from datetime import datetime, timedelta
from kubernetes import client, config

# Connect to Prometheus
# Kubernetes Config
config.load_kube_config()
v1 = client.CoreV1Api()

# Prometheus Config
#prom_url = "http://<PROMETHEUS_SERVER_IP>:<PORT>"
# prom_url = "http://10.110.188.57:9090"
prom_url = "http://10.105.116.175:9090"

prom = PrometheusConnect(url=prom_url, disable_ssl=True)
#test prom connection
prom_connect_response = prom.custom_query(query="up")
if not prom_connect_response:
    raise Exception("Failed to connect to Prometheus")


'''@@@@@@@@@@@@2@@@@@@@@@'''
from prometheus_api_client import PrometheusConnect, MetricRangeDataFrame
from datetime import datetime, timedelta
from kubernetes import client, config
import re
import pandas as pd

def get_metrics_data(lookback_min= 0, time_range="10m", rate_parameter="1m", query_step="10s"):
    # Connect to Prometheus
    config.load_kube_config()
    v1 = client.CoreV1Api()

    # Prometheus Config
    prom_url = "http://10.105.116.175:9090"
    prom = PrometheusConnect(url=prom_url, disable_ssl=True)

    # Test Prometheus connection
    prom_connect_response = prom.custom_query(query="up")
    if not prom_connect_response:
        raise Exception("Failed to connect to Prometheus")

    # Define the namespace
    namespace = 'social-network'

    # Parse time_range to get timedelta
    time_value, time_unit = int(re.match(r"(\d+)", time_range).group(0)), re.match(r"(\d+)(\D+)", time_range).group(2)
    time_delta_map = {'s': 'seconds', 'm': 'minutes', 'h': 'hours', 'd': 'days'}
    time_kwargs = {time_delta_map[time_unit]: time_value}
    time_range_delta = timedelta(**time_kwargs)

    end_time = datetime.now() -timedelta(minutes=lookback_min)
    start_time = end_time - time_range_delta

    # Define Prometheus queries for response time and throughput
    response_time_query = f"rate(istio_request_duration_milliseconds_sum{{namespace='{namespace}',response_code='200'}}[{rate_parameter}]) / rate(istio_requests_total{{namespace='{namespace}',response_code='200'}}[{rate_parameter}])"
    throughput_query = f"rate(istio_requests_total{{namespace='{namespace}',response_code='200'}}[{rate_parameter}])"

    # Fetch metrics data
    response_time_data = prom.custom_query_range(
        query=response_time_query,
        start_time=start_time,
        end_time=end_time,
        step=query_step
    )
    throughput_data = prom.custom_query_range(
        query=throughput_query,
        start_time=start_time,
        end_time=end_time,
        step=query_step
    )

    # Convert to DataFrame for easy manipulation
    response_time_df = MetricRangeDataFrame(response_time_data)
    throughput_df = MetricRangeDataFrame(throughput_data)

    # Remove NaN values
    response_time_df = response_time_df.dropna()
    throughput_df = throughput_df.dropna()
    
    # Remove '0' values 
    # for throughput (it will be inaccurate to counts all values with '0' when calculating average)
    throughput_df = throughput_df[throughput_df['value'] !=0]
    response_time_df = response_time_df[response_time_df['value'] !=0]


    # Calculate average response time and throughput
    average_response_time = response_time_df['value'].mean()
    average_throughput = throughput_df['value'].mean()

    return response_time_df, throughput_df, average_response_time, average_throughput



'''############3#######'''

'''Workload Sending
three different Requests of social network; QPS, Users
'''

import subprocess,time

# compos-post request
url_1 = "http://nginx-thrift.social-network.svc.cluster.local:8080/wrk2-api/post/compose"
script_path_1 = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/compose-post.lua"  


# read-home-timeline request
url_2 = "http://nginx-thrift.social-network.svc.cluster.local:8080/wrk2-api/home-timeline/read"
script_path_2 = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/read-home-timeline.lua"

# read-user-timeline request
url_3 = "http://nginx-thrift.social-network.svc.cluster.local:8080/wrk2-api/user-timeline/read"
script_path_3 = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/read-user-timeline.lua"


url= [url_1, url_2, url_3]
script_path = [script_path_1, script_path_2, script_path_3]
req_rates = [[50, 100, 200], # compose-post rquest rate; bottleneck ~250 req/s
            [200, 500, 1000], # read-home-timeline request rate
            [200, 500, 1000] # read-user-timeline request rate
            ]
# req_rates=[[10,20], [50,100], [60,120]]
duration = '30s'

for i in range(len(url)):
    for req in req_rates[i]: # req_rates[i] for url[i]
        # for req in j: # using different rate for different requests
        command = f"/home/ubuntu/DeathStarBench/wrk2/wrk -D -t2 -c100 -d{duration} -L -s {script_path[i]} {url[i]} -R{req}"
        result = subprocess.run(command, shell=True)
        
        # Optional sleep to allow metrics to stabilize/propagate
        # time.sleep(30)  # Sleep seconds
        
        
        #when the above comand is finished and print out the result, run the following:        
        response_time_df, throughput_df, average_response_time, average_throughput = get_metrics_data(
            lookback_min=0, time_range="30s", rate_parameter="30s", query_step="10s")
        print(f"Current Req is: {req} reqs/second")
        print(f"Average Response Time: {average_response_time} ms")
        print(f"Average Throughput: {average_throughput} requests/second")      