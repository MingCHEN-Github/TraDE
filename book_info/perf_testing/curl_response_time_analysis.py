#!/usr/bin/env python3

# Ming Chen, 18 March, 2024
# cURL request and response time for bookinfo microservice app

from tqdm import tqdm
from time import sleep
import subprocess, csv, time, os

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Function to make curl request and parse its output
def make_curl_request(url):
    cmd = [
        'curl', # '--max-time', '8',,,  Set the currl request maximum time to ' ' seconds
        '-o', '/dev/null', '-s', '-w',
        "%{http_code},%{time_namelookup},%{time_connect},%{time_appconnect},%{time_pretransfer},%{time_redirect},%{time_starttransfer},%{time_total}\n",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

def make_curl_request_successful(url):
    cmd = [
        'curl', '-m', '0.2',  # Adjusted max time to a plausible value
        '-o', '/dev/null', '-s', '-w',
        "%{http_code},%{time_namelookup},%{time_connect},%{time_appconnect},%{time_pretransfer},%{time_redirect},%{time_starttransfer},%{time_total}\n",
        url
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    http_code = result.stdout.split(',')[0]
    
    # Check if the response was successful (HTTP status code 200)
    if http_code == "200":
        return result.stdout
    else:
        return None

# Num of requests as the parameter: Save curl response information to a CSV file with progress bar
def ReqNum_save_responses_to_csv(url, num_requests, filename):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['http_code', 'time_namelookup', 'time_connect', 'time_appconnect', 'time_pretransfer', 'time_redirect', 'time_starttransfer', 'time_total'])
        
        for _ in tqdm(range(num_requests), desc="Sending Requests", unit="request"):
            '''
            return all respones or just the successful
            '''
            response = make_curl_request(url)
            # response = make_curl_request_successful(url)
            
            #skip the unsuccessful response (eg, timeout)
            if response:
                writer.writerow(response.strip().split(','))

# Request sending rate and the duration as the parameter: 
def ReqSpeed_save_responses_to_csv(url, request_rate, duration_seconds, filename):
    interval = 1.0 / request_rate  # Time between requests to achieve the target rate
    total_requests = int(request_rate * duration_seconds)  # Calculate total requests based on the duration

    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['http_code', 'time_namelookup', 'time_connect', 'time_appconnect', 'time_pretransfer', 'time_redirect', 'time_starttransfer', 'time_total'])
        
        for _ in tqdm(range(total_requests), desc="Sending Requests", unit="request"):
            start_time = time.time()
            response = make_curl_request(url)
            writer.writerow(response.strip().split(','))
            end_time = time.time()
            
            # Wait for the next request, adjusting for the time spent on the current request
            sleep(max(0, interval - (end_time - start_time)))



# Read the CSV file and calculate percentiles for the time_total column
def plot_percentiles_from_csv(filename, figname):
    data = pd.read_csv(filename)
    p90 = np.percentile(data['time_total'], 90)
    p95 = np.percentile(data['time_total'], 95)
    p99 = np.percentile(data['time_total'], 99)

    # Plotting
    plt.figure(figsize=(10, 6))
    sorted_data = np.sort(data['time_total'])
    plt.step(sorted_data, np.linspace(0, 1, len(sorted_data), endpoint=False), label='CDF', where='post')

    # Highlight p90, p95, and p99
    # plt.axvline(x=p90, color='blue', linestyle='--', label=f'p90 ({p90:.4f}s)')
    plt.axvline(x=p90, color='blue', linestyle='--', label=f'p90 ({p90:.4f}s)')
    plt.axvline(x=p95, color='green', linestyle='--', label=f'p95 ({p95:.4f}s)')
    plt.axvline(x=p99, color='red', linestyle='--', label=f'p99 ({p99:.4f}s)')

    plt.xlabel('Response Time (seconds)')
    plt.ylabel('CDF')
    plt.title('CDF of Response Times with p90, p95, p99 Highlighted')
    plt.legend()
    plt.grid(True)
    
    plt.savefig(figname)
    plt.close()
    
'''
write in one function to run curl testing
'''

def run_curl(Req_num = 100):
    # Getting the Gateway Url
    INGRESS_PORT = os.popen(
    "kubectl -n istio-system get service istio-ingressgateway -o jsonpath=\"{.spec.ports[?(@.name=='http2')].nodePort}\""
    ).read().strip()
    SECURE_INGRESS_PORT = os.popen(
    "kubectl -n istio-system get service istio-ingressgateway -o jsonpath=\"{.spec.ports[?(@.name=='https')].nodePort}\""
    ).read().strip()

    INGRESS_HOST = os.popen(
    'kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath="{.items[0].status.hostIP}"'
    ).read().strip()

    # the reuqesting url
    # run the command at terminal:   curl -v http://172.26.130.82:32428/productpage  -w "@performance-format.txt" -o response_return.txt

    GATEWAY_URL = f"http://{INGRESS_HOST}:{INGRESS_PORT}/productpage" #  http://172.26.130.82:32428/productpage
    # ReqA_URL = f"http://{INGRESS_HOST}:{INGRESS_PORT}/productpage/review-v1"

    Data_path = '/home/ubuntu/ms_scheduling/book_info/perf_testing/data/' # saving the performance tesing data to this path


    REQUEST_NUM = Req_num
    REQUEST_SPEED = 100 # 1000 req/ second
    TIME_DURATION =200

    current_time_str = time.strftime("%m%d%H%M")  # Format: MonthDayHourMinute


    print("Starting script at", time.ctime())
    csv_filename = Data_path + f"{current_time_str}_Req{REQUEST_NUM}_responses.csv"
    fig_name = Data_path +f"{current_time_str}_Req{REQUEST_NUM}_Response_times_cdf.png"
    ReqNum_save_responses_to_csv(url=GATEWAY_URL, num_requests=REQUEST_NUM, filename=csv_filename)



    # csv_filename = Data_path + f"{current_time_str}_Req{REQUEST_SPEED}Rps_{TIME_DURATION}s_curl.csv"
    # fig_name = Data_path +f"{current_time_str}_Req{REQUEST_SPEED}_Response_times_cdf.png"
    # ReqSpeed_save_responses_to_csv(url=GATEWAY_URL, request_rate=REQUEST_SPEED, duration_seconds=TIME_DURATION, filename=csv_filename)


    plot_percentiles_from_csv(csv_filename, fig_name)
    print("Script finished and plot saved at", time.ctime())


for i in [100, 500, 1000, 1500]:
    run_curl(Req_num=i)