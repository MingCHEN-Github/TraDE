import subprocess
import os
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm
import seaborn as sns

# Function to execute wrk command
def run_wrk(url, script_path, duration, rate, data_dir):
    current_time_str = datetime.now().strftime("%Y%m%d%H%M")
    result_filename = f"{data_dir}/{current_time_str}_{rate}_{duration}.txt"
    # command = f"/home/ubuntu/DeathStarBench/wrk2/wrk -D exp -t2 -c100 -d{duration} -L -s {script_path} {url} -R{rate}"
    
    #use constant rate
    command = f"/home/ubuntu/DeathStarBench/wrk2/wrk -D -t2 -c100 -d{duration} -L -s {script_path} {url} -R{rate}"

    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    with open(result_filename, 'w') as file:
        file.write(result.stdout)
    
    print(f"Results for rate {rate} saved to {result_filename}")
    return result_filename

# Function to parse wrk output
def parse_wrk_output(filename):
    latencies = []
    recording = False  # Flag to start recording latencies
    with open(filename, 'r') as file:
        for line in file:
            if line.startswith("  Detailed Percentile spectrum:"):
                recording = True
                continue
            if line.startswith("#[Mean"):
                break
            if recording:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        latency = float(parts[0])
                        latencies.append(latency)
                    except ValueError:
                        continue
    return latencies

# Function to plot CDF
def plot_cdf(data, filename):
    sorted_data = np.sort(data)
    plt.figure(figsize=(10, 6))
    plt.step(sorted_data, np.linspace(0, 1, len(sorted_data), endpoint=False), where='post')
    plt.xlabel('Response Time (ms)')
    plt.ylabel('CDF')
    plt.title('CDF of Response Times')
    plt.grid(True)
    plt.savefig(filename)
    plt.close()

# Function to plot Violin Plot
def plot_violin(latency_data, request_rates, data_dir):
    plt.figure(figsize=(12, 8))
    data_to_plot = [latencies for _, latencies in latency_data.items() if latencies]
    sns.violinplot(data=data_to_plot)
    plt.xticks(np.arange(len(request_rates)), labels=[str(rate) for rate in request_rates])
    plt.xlabel('Request Rate')
    plt.ylabel('Response Time (*1000 ms)')
    plt.title('Response Time Distribution by Request Rate')
    plt.grid(True)
    
    current_time_str = datetime.now().strftime("%Y%m%d%H%M")
    filename = f"{data_dir}/violin_plot_{current_time_str}.png"
    plt.savefig(filename)
    plt.close()
    print(f"Saved violin plot to {filename}")

def main():
    # data_dir = "/home/ubuntu/ms_scheduling/social_net/perf_testing/data"
    data_dir_1 =  "/home/ubuntu/ms_scheduling/social_net/evaluations/knee_point/data_composePost"
    os.makedirs(data_dir_1, exist_ok=True)
    
    data_dir_2 =  "/home/ubuntu/ms_scheduling/social_net/evaluations/knee_point/data_readHometime"
    os.makedirs(data_dir_2, exist_ok=True)

    # compos-post request
    url_1 = "http://nginx-thrift.social-network.svc.cluster.local:8080/wrk2-api/post/compose"
    script_path_1 = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/compose-post.lua"  
    
    
    # read-home-timeline request
    url_2 = "http://nginx-thrift.social-network.svc.cluster.local:8080/wrk2-api/home-timeline/read"
    script_path_2 = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/read-home-timeline.lua"
    
     
    
    duration = "1m"
    request_rates = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500, 550,
                     600, 700, 800, 900, 1000, 1200, 1400, 1600, 1800, 2000]
    # request_rates= [10, 20, 30]
    
    # Use a for loop to generate the above QPS list
    # request_rates = [i for i in range(50, 2000 + 1, 100)]
    
    request_url = [url_1, url_2]
    request_script_path = [script_path_1, script_path_2]
    saving_data_dir = [data_dir_1, data_dir_2]
    
    input_meta =[request_url, request_script_path, saving_data_dir]
    
    
    # loop testing for different requests and save the perf data
    for i in range(len(request_url)): # total types of testing requests
        url = input_meta[0][i]
        script_path = input_meta[1][i]
        data_dir = input_meta[2][i]
        
         
        result_files = []
        latency_data = {}
        p99_latencies = []

        for rate in tqdm(request_rates, desc="Running wrk for different rates"):
            
            filename = run_wrk(url, script_path, duration, rate, data_dir)
            latencies = parse_wrk_output(filename)
            latency_data[rate] = latencies
            if latencies:
                # plot_filename = filename.replace('.txt', '_cdf.png')
                # plot_cdf(latencies, plot_filename)
                p99_latencies.append(np.percentile(latencies, 99))  # Calculate and store the p99 latency
                # avg_latency = np.mean(latencies)
                # p99_latencies.append(avg_latency)

        # Plot the p99 latency line plot
        if p99_latencies:
            plt.figure(figsize=(10, 6))
            plt.plot(request_rates, [latency / 1000 for latency in p99_latencies], marker='o', linestyle='-', color='red')
            plt.xlabel('Request Rate')
            plt.ylabel('p99 Latency (*1000 ms)')
            plt.title('p99 Latency by Request Rate')
            plt.grid(True)
            
            current_time_str = datetime.now().strftime("%Y%m%d%H%M")
            filename = f"{data_dir}/p99_latency_plot_{current_time_str}.png"
            plt.savefig(filename)
            plt.close()
            print(f"Saved p99 latency plot to {filename}")

        if latency_data:
            plot_violin(latency_data, request_rates, data_dir)

if __name__ == "__main__":
    main()
