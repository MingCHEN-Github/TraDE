#!/usr/bin/env python3

# Ming Chen, 18 March, 2024
# wrk http request load testing for Social Network (DeathStarBench) microservice app

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
    command = f"/home/ubuntu/DeathStarBench/wrk2/wrk -D exp -t2 -c100 -d{duration} -L -s {script_path} {url} -R{rate}"
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
            # Start recording after the "Detailed Percentile spectrum:" line
            if line.startswith("  Detailed Percentile spectrum:"):
                recording = True
                continue  # Skip the header line
            # Stop recording at the summary statistics section
            if line.startswith("#[Mean"):
                break
            if recording:
                # Example line: "       2.037     0.000000            1         1.00"
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        # Assuming latencies are reported in milliseconds
                        latency = float(parts[0])  # Convert latency value to float
                        latencies.append(latency)
                    except ValueError:
                        # Handle the case where conversion to float fails
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
    plt.ylabel('Response Time (ms)')
    plt.title('Response Time Distribution by Request Rate')
    plt.grid(True)
    
    current_time_str = datetime.now().strftime("%Y%m%d%H%M")
    filename = f"{data_dir}/violin_plot_{current_time_str}.png"
    plt.savefig(filename)
    plt.close()
    print(f"Saved violin plot to {filename}")

def main():
    data_dir = "/home/ubuntu/ms_scheduling/social_net/perf_testing/data"
    os.makedirs(data_dir, exist_ok=True)

    url = "http://nginx-thrift.social-network.svc.cluster.local:8080/wrk2-api/home-timeline/read"
    script_path = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/read-home-timeline.lua"
    duration = "1m"
    request_rates = [100, 500, 1000, 2000]
    result_files = []
    latency_data = {}

    for rate in tqdm(request_rates, desc="Running wrk for different rates"):
        filename = run_wrk(url, script_path, duration, rate, data_dir)
        latencies = parse_wrk_output(filename)
        latency_data[rate] = latencies
        if latencies:
            plot_filename = filename.replace('.txt', '_cdf.png')
            plot_cdf(latencies, plot_filename)

    average_response_times = []
    for rate, latencies in latency_data.items():
        if latencies:
            avg_latency = np.mean(latencies)
            average_response_times.append(avg_latency)
    
    if average_response_times:
        plt.figure(figsize=(10, 6))
        plt.bar([str(rate) for rate in request_rates], average_response_times, color='skyblue')
        plt.xlabel('Request Rate')
        plt.ylabel('Average Response Time (ms)')
        plt.title('Average Response Time by Request Rate')
        plt.grid(True)
        
        current_time_str = datetime.now().strftime("%Y%m%d%H%M")
        filename = f"{data_dir}/average_RT_comparison_{current_time_str}.png"
        plt.savefig(filename)
        plt.close()
        print(f"Saved average response time plot to {filename}")

    if latency_data:
        plot_violin(latency_data, request_rates, data_dir)

if __name__ == "__main__":
    main()













# #!/usr/bin/env python3

# # Ming Chen, 18 March, 2024
# # wrk http request load testing for Social Network (DeathStarBench) microservice app


# import subprocess
# import os
# from datetime import datetime
# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
# from tqdm import tqdm
# import seaborn as sns

# # Function to execute wrk command
# def run_wrk(url, script_path, duration, rate, data_dir):
#     current_time_str = datetime.now().strftime("%Y%m%d%H%M")
#     result_filename = f"{data_dir}/{current_time_str}_{rate}_{duration}.txt"
#      # wrk command is located at /home/ubuntu/DeathStarBench/wrk2/
#     command = f"/home/ubuntu/DeathStarBench/wrk2/wrk -D exp -t2 -c100 -d{duration} -L -s {script_path} {url} -R{rate}"
#     result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
#     with open(result_filename, 'w') as file:
#         file.write(result.stdout)
    
#     print(f"Results for rate {rate} saved to {result_filename}")
#     return result_filename

# # Function to parse wrk output
# def parse_wrk_output(filename):
#     latencies = []
#     recording = False  # Flag to start recording latencies
#     with open(filename, 'r') as file:
#         for line in file:
#             # Start recording after the "Detailed Percentile spectrum:" line
#             if line.startswith("  Detailed Percentile spectrum:"):
#                 recording = True
#                 continue  # Skip the header line

#             # Stop recording at the summary statistics section
#             if line.startswith("#[Mean"):
#                 break

#             if recording:
#                 # Example line: "       2.037     0.000000            1         1.00"
#                 parts = line.split()
#                 if len(parts) >= 2:
#                     try:
#                         # Assuming latencies are reported in milliseconds
#                         latency = float(parts[0])  # Convert latency value to float
#                         latencies.append(latency)
#                     except ValueError:
#                         # Handle the case where conversion to float fails
#                         continue

#     return latencies


# # Function to plot CDF
# def plot_cdf(data, filename):
#     sorted_data = np.sort(data)
#     plt.figure(figsize=(10, 6))
#     plt.step(sorted_data, np.linspace(0, 1, len(sorted_data), endpoint=False), where='post')
#     plt.xlabel('Response Time (ms)')
#     plt.ylabel('CDF')
#     plt.title('CDF of Response Times')
#     plt.grid(True)
#     plt.savefig(filename)
#     plt.close()

# # function to plot Violin plot with different Request_Rate
# def plot_violin(latency_data, request_rates, data_dir):
#     """
#     Plots a violin plot for the latency distributions across different request rates.

#     :param latency_data: A dictionary where keys are request rates and values are lists of latencies.
#     :param request_rates: A list of request rates.
#     :param data_dir: Directory to save the plot.
#     """
#     plt.figure(figsize=(12, 8))
#     # Prepare data for plotting
#     data_to_plot = []
#     labels = []
#     for rate, latencies in latency_data.items():
#         if latencies:  # Ensure there's data to plot
#             data_to_plot.append(latencies)
#             labels.append(str(rate))
    
#     # Plotting the violin plot
#     sns.violinplot(data=data_to_plot)
#     plt.xticks(np.arange(len(labels)), labels)
#     plt.xlabel('Request Rate')
#     plt.ylabel('Response Time (ms)')
#     plt.title('Response Time Distribution by Request Rate')
#     plt.grid(True)

#     # Save the plot
#     current_time_str = datetime.now().strftime("%Y%m%d%H%M")
#     filename = f"{data_dir}/violin_plot_{current_time_str}.png"
#     plt.savefig(filename)
#     plt.close()
#     print(f"Saved violin plot to {filename}")


# def main():
#     data_dir = "/home/ubuntu/ms_scheduling/social_net/perf_testing/data"
#     os.makedirs(data_dir, exist_ok=True)

#     url = "http://nginx-thrift.social-network.svc.cluster.local:8080/wrk2-api/home-timeline/read"
#     script_path = "/home/ubuntu/DeathStarBench/socialNetwork/wrk2/scripts/social-network/read-home-timeline.lua"
#     duration = "10m"
#     request_rates = [300, 500, 1000, 1500, 2000, 3000, 5000]
#     result_files = []
    
#     latency_data = {}  # Initialize a dictionary to store latency data for each rate

    

#     # step1: Execute wrk and PLot CDF figures
#     for rate in tqdm(request_rates, desc="Running wrk for different rates"):
#         filename = run_wrk(url, script_path, duration, rate, data_dir)
#         latencies = parse_wrk_output(filename)
#         if latencies:
#             latency_data[rate] = latencies  # Store latencies for this rate
#             plot_filename = filename.replace('.txt', '_cdf.png')
#             plot_cdf(latencies, plot_filename)

#     # Step2: Calculate and Plot Average Response Time Comparison
#     average_response_times = []
#     for filename in tqdm(result_files, desc="Calculating avg response times"):
#         latencies = parse_wrk_output(filename)
#         if latencies:  # Check if the list is not empty
#             avg_latency = np.mean(latencies)
#             average_response_times.append(avg_latency)

#     if average_response_times:  # Check if the list is not empty
#         plt.figure(figsize=(10, 6))
#         plt.bar([str(rate) for rate in request_rates], average_response_times, color='skyblue')
#         plt.xlabel('Request Rate')
#         plt.ylabel('Average Response Time (ms)')
#         plt.title('Average Response Time by Request Rate')
#         plt.grid(True)
        
#           # Get current time and format it
#         current_time_str = datetime.now().strftime("%Y%m%d%H%M")
#         filename = f"{data_dir}/average_RT_comparison_{current_time_str}.png"
    
#         plt.savefig(filename)
#         plt.close()
    
#     # plot violion figures
#     if latency_data:
#         plot_violin(latency_data, request_rates, data_dir)
# #ploting histogram data from wrk command output results
# # https://hdrhistogram.github.io/HdrHistogram/plotFiles.html

# if __name__ == "__main__":
#     main()
