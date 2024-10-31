'''
copy/modify the following load_test code into the running UM client pod (deployed by UM_client.yaml)
'''







'''calcuate the knee-point by using p99 response time with varying qps'''


# run inside the client pod
import requests
import time
import numpy as np
import matplotlib.pyplot as plt

# Server endpoint
url = "http://server-service.client-server.svc.cluster.local"

# Different queries per second
qps_values = [10000, 20000, 50000, 100000, 200000, 500000, 1000000,5000000]
test_duration_seconds = 5  # 2 minutes per QPS
percentiles = {'p50': [], 'p90': [], 'p99': []}

for qps in qps_values:
    response_times = []
    start_test = time.time()

    while (time.time() - start_test) < test_duration_seconds:
        start_time = time.time()
        try:
            response = requests.get(url)
            response.raise_for_status()  # This will raise an exception for HTTP error codes
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000  # Convert response time to milliseconds
            response_times.append(response_time_ms)
            # Sleep to maintain the QPS rate
            sleep_time = max(0, (1 / qps) - (end_time - start_time))
            time.sleep(sleep_time)
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            # Continue to maintain QPS even after a failed request
            end_time = time.time()
            sleep_time = max(0, (1 / qps) - (end_time - start_time))
            time.sleep(sleep_time)

    # Calculate percentiles
    if response_times:
        percentiles['p50'].append(np.percentile(response_times, 50))
        percentiles['p90'].append(np.percentile(response_times, 90))
        percentiles['p99'].append(np.percentile(response_times, 99))
    else:
        # percentiles['p50'].append(float('inf'))
        # percentiles['p90'].append(float('inf'))
        percentiles['p99'].append(float('inf'))

    print(f"QPS: {qps}, P50: {percentiles['p50'][-1]:.2f} ms, P90: {percentiles['p90'][-1]:.2f} ms, P99: {percentiles['p99'][-1]:.2f} ms")

# Save the data to a file
all_data = [] # save all [qps, p99] data pair
with open('response_times.csv', 'w') as f:
    # f.write('QPS,p50,p90,p99\n')
    for i, qps in enumerate(qps_values):
        f.write(f"{qps},{percentiles['p50'][i]:.2f},{percentiles['p90'][i]:.2f},{percentiles['p99'][i]:.2f}\n")
        f.write(f"[QPS, p99]= [{qps}, {percentiles['p99'][i]:.2f}]\n")
        all_data.append([qps, int(percentiles['p99'][i])])


# print all data in a row like [pqs,p99]
print(all_data)




# '''Output P99 response time'''

# import requests
# import time
# import numpy as np

# # Server endpoints
# url1 = "http://server-service.client-server.svc.cluster.local"  # Client pod and server pod are at different nodes
# url2 = "http://server-service2.client-server.svc.cluster.local"  # Client pod and server pod are at same nodes

# urls = [url1, url2]
# qps_values = [500, 1000, 3000, 5000]  # Different queries per second
# test_duration_seconds = 5  # Test duration in seconds for each message size and QPS level

# message_sizes = [256, 1024, 4096, 16384, 65536, 262144, 1048576]  # Message sizes in Bytes

# # Store results in a structured format
# results = {qps: {ms: [] for ms in message_sizes} for qps in qps_values}

# for qps in qps_values:
#     print(f"Testing at QPS: {qps}")
#     for message_size in message_sizes:
#         summary = []
#         for url in urls:
#             message = 'x' * message_size  # Create a message of 'x' repeated to the desired size
#             response_times = []
#             start_test = time.time()

#             while (time.time() - start_test) < test_duration_seconds:
#                 start_time = time.time()
#                 try:
#                     # Use POST to send data
#                     response = requests.post(url + "/post", data=message)
#                     response.raise_for_status()  # Check for HTTP errors
#                     end_time = time.time()
#                     response_time_ms = (end_time - start_time) * 1000  # Convert response time to milliseconds
#                     response_times.append(response_time_ms)
#                 except requests.RequestException as e:
#                     print(f"Request failed: {e}")
#                 finally:
#                     # Sleep to maintain the QPS rate
#                     end_time = time.time()
#                     sleep_time = max(0, (1 / qps) - (end_time - start_time))
#                     time.sleep(sleep_time)

#             # Calculate P99 latency for the current URL and message size
#             p99_latency = np.percentile(response_times, 99) if response_times else float('inf')
#             summary.append(p99_latency)

#         # Store results for this message size
#         results[qps][message_size] = summary
#         print(f"Message Size: {message_size} bytes, URL1 P99: {summary[0]:.2f} ms, URL2 P99: {summary[1]:.2f} ms")

# #print all collected data at the end
# for qps, data in results.items():
#     print(f"QPS: {qps}")
#     for ms, times in data.items():
#         print(f"Message Size: {ms} bytes, URL1 P99 and URL2 P99 are: [{times[0]:.2f}, {times[1]:.2f}]")




# '''Output average_response time


# # ouput average response time
# import requests
# import time
# import numpy as np

# # Server endpoints
# url1 = "http://server-service.client-server.svc.cluster.local"  # Client pod and server pod are at different nodes
# url2 = "http://server-service2.client-server.svc.cluster.local"  # Client pod and server pod are at same nodes

# urls = [url1, url2]
# qps_values = [1000, 3000, 5000]  # Different queries per second
# test_duration_seconds = 1  # Test duration in seconds for each message size and QPS level

# message_sizes = [256, 1024, 4096, 16384, 65536, 262144, 1048576]  # Message sizes in Bytes

# # Store results in a structured format
# results = {qps: {ms: [] for ms in message_sizes} for qps in qps_values}

# for qps in qps_values:
#     print(f"Testing at QPS: {qps}")
#     for message_size in message_sizes:
#         summary = []
#         for url in urls:
#             message = 'x' * message_size  # Create a message of 'x' repeated to the desired size
#             response_times = []
#             start_test = time.time()

#             while (time.time() - start_test) < test_duration_seconds:
#                 start_time = time.time()
#                 try:
#                     # Use POST to send data
#                     response = requests.post(url + "/post", data=message)
#                     response.raise_for_status()  # Check for HTTP errors
#                     end_time = time.time()
#                     response_time_ms = (end_time - start_time) * 1000  # Convert response time to milliseconds
#                     response_times.append(response_time_ms)
#                 except requests.RequestException as e:
#                     print(f"Request failed: {e}")
#                 finally:
#                     # Sleep to maintain the QPS rate
#                     end_time = time.time()
#                     sleep_time = max(0, (1 / qps) - (end_time - start_time))
#                     time.sleep(sleep_time)

#             # Calculate average response time for the current URL and message size
#             avg_response_time = np.mean(response_times) if response_times else float('inf')
#             summary.append(avg_response_time)

#         # Store results for this message size
#         results[qps][message_size] = summary
#         print(f"Message Size: {message_size} bytes, URL1 Avg: {summary[0]:.2f} ms, URL2 Avg: {summary[1]:.2f} ms")

# # Optionally, print all collected data at the end
# for qps, data in results.items():
#     print(f"QPS: {qps}")
#     for ms, times in data.items():
#         print(f"Message Size: {ms} bytes, URL1 Avg and URL2 Avg are: [{times[0]:.2f} , {times[1]:.2f}]")




# '''


# import requests
# import time
# import numpy as np

# # Server endpoint
# url1 = "http://server-service.client-server.svc.cluster.local" # client pod and server pod are at different nodes
# url2 = "http://server-service2.client-server.svc.cluster.local"  # client pod and server pod are at same nodes

# urls = [url1, url2]

# # Different queries per second
# qps_values = [1000, 3000, 5000]  # Corrected list format
# test_duration_seconds = 10  # 1 minute per QPS

# # percentiles = {'p50': [], 'p90': [], 'p99': [], 'avg' : []}
# percentiles = {'p99': [], 'avg' : []}

# message_sizes = [256, 1024,4*1024, 16*1024, 64*1024, 256*1024, 1024*1024]  # in Bytes



# for qps in qps_values: # from low to high
#     for url in urls: # send to server1 (different node) and then server 2 (same node)
#         for message_size in message_sizes:
#             message = 'x' * message_size  # Create a message of 'x' repeated to the desired size
#             # for url in urls: # send to server1 (different node) and then server 2 (same node)
#             response_times = []
#             start_test = time.time()

#             while (time.time() - start_test) < test_duration_seconds:
#                 start_time = time.time()
#                 try:
#                     # Use POST to send data
#                     response = requests.post(url + "/post", data=message)
#                     response.raise_for_status()  # This will raise an exception for HTTP error codes
#                     end_time = time.time()
#                     response_time_ms = (end_time - start_time) * 1000  # Convert response time to milliseconds
#                     response_times.append(response_time_ms)
#                     # Sleep to maintain the QPS rate
#                     sleep_time = max(0, (1 / qps) - (end_time - start_time))
#                     time.sleep(sleep_time)
#                 except requests.RequestException as e:
#                     print(f"Request failed: {e}")
#                     # Continue to maintain QPS even after a failed request
#                     end_time = time.time()
#                     sleep_time = max(0, (1 / qps) - (end_time - start_time))
#                     time.sleep(sleep_time)

#             # Calculate percentiles and average
#             if response_times:
#                 percentiles['p99'].append(np.percentile(response_times, 99))
#                 percentiles['avg'].append(np.mean(response_times))
#             else:
#                 percentiles['p99'].append(float('inf'))
#                 percentiles['avg'].append(float('inf'))
                
#             print(f" QPS: {qps},  URL: {url}, Message Size: {message_size} bytes, Avg: {percentiles['avg'][-1]:.2f} ms, P99: {percentiles['p99'][-1]:.2f} ms")

    # Print final summary
    # print("QPS Values:", qps_values)
    # print(f"P99 Response Times for each message size:, {percentiles['p99'][-1]:.2f} ")
    # print(f"Average Response Times for each message size:, {percentiles['avg'][-1]:.2f} ")
