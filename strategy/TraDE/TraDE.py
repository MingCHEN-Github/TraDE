from kubernetes import client, config, stream
import pandas as pd
import matplotlib.pyplot as plt

from prometheus_api_client import PrometheusConnect

from datetime import datetime, timedelta
from difflib import diff_bytes

import seaborn as sns
import numpy as np
import random
import multiprocessing as mp
from timeit import default_timer as timer
from datetime import datetime, timedelta

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
print(prom_connect_response)



'''trigger decision'''

import time
from datetime import datetime, timedelta
from urllib import response

# Configurable parameters
QoS_target = 300  # QoS target (ms) from knee point analysis, specific to the application
time_window = 1  # Time window in minutes
_Namespace = 'social-network3'
response_code = '200'  # Consider only successful responses (HTTP 200)

# Define the time range for the query
end_time = datetime.now() - timedelta(minutes=0)  # Current time minus ten minutes,,  - timedelta(minutes=10)
start_time = end_time - timedelta(minutes=time_window)  # Start time is 'time_window' minutes before end time

def trigger_migration(QoS_target, time_window, app_namespace):
    trigger = False
    step = str(time_window * 60)  # Step size in seconds for Prometheus queries

    # Prometheus queries for Istio metrics
    istio_request_duration_query = f'rate(istio_request_duration_milliseconds_sum{{namespace="{app_namespace}", response_code="{response_code}"}}[{time_window}m])'
    istio_requests_total_query = f'rate(istio_requests_total{{namespace="{app_namespace}", response_code="{response_code}"}}[{time_window}m])'

    # Fetch the data from Prometheus
    istio_request_duration_response = prom.custom_query_range(
        query=istio_request_duration_query,
        start_time=start_time,
        end_time=end_time,
        step=step
    )
    istio_requests_total_response = prom.custom_query_range(
        query=istio_requests_total_query,
        start_time=start_time,
        end_time=end_time,
        step=step
    )

    # Ensure there is data to process
    if istio_request_duration_response and istio_requests_total_response:
        duration_values = [float(val[1]) for val in istio_request_duration_response[0]['values']]
        total_requests_values = [float(val[1]) for val in istio_requests_total_response[0]['values']]

        if total_requests_values and duration_values:
            # Compute the average response time in milliseconds
            total_requests_sum = sum(total_requests_values)
            if total_requests_sum > 0:
                average_response_time = sum(duration_values) / total_requests_sum
                print(f"Average response time = {average_response_time:.2f} ms")

                # Check if the average response time exceeds the QoS target
                if average_response_time > QoS_target:
                    trigger = True
            else:
                print("Total requests sum is zero, cannot compute average response time.")
        else:
            print("No traffic detected, no trigger.")
    else:
        print("Query returned no data, no trigger.")

    
    print(f"Trigger = {trigger}")

    return trigger

# Example usage
trigger_migration(QoS_target=QoS_target, time_window=time_window, app_namespace=_Namespace)




'''Building traffic Stress graph, return the ms execution graph with bi-direction traffic '''
# Function to retrieve ready deployments
def get_ready_deployments(namespace):
    ready_deployments = []
    deployments = client.AppsV1Api().list_namespaced_deployment(namespace)
    for deployment in deployments.items:
        if deployment.status.ready_replicas == deployment.spec.replicas:
            ready_deployments.append(deployment.metadata.name)
    return ready_deployments

# Function to calculate transmitted requests
def transmitted_req_calculator(workload_src, workload_dst, timerange, step_interval, app_namespace):
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=timerange)

    istio_tcp_sent_query = f'istio_tcp_sent_bytes_total{{reporter="source",source_workload="{workload_src}",destination_workload="{workload_dst}", namespace = "{app_namespace}"}}'
    istio_tcp_received_query = f'istio_tcp_received_bytes_total{{reporter="source",source_workload="{workload_src}",destination_workload="{workload_dst}", namespace = "{app_namespace}"}}'

    istio_tcp_sent_response = prom.custom_query_range(
        query=istio_tcp_sent_query,
        start_time=start_time,
        end_time=end_time,
        step=step_interval
    )
    istio_tcp_received_response = prom.custom_query_range(
        query=istio_tcp_received_query,
        start_time=start_time,
        end_time=end_time,
        step=step_interval
    )

    # only calculate the from {workload_src} to {workload_dst} that have no traffic.
    if (not istio_tcp_sent_response or not istio_tcp_sent_response[0]['values']) and (not istio_tcp_received_response or not istio_tcp_received_response[0]['values']):
        # print(f'from {workload_src} to {workload_dst} average_traffic_bytes: no values' )
        return 0
    else:
        values_sent = istio_tcp_sent_response[0]['values']
        values_received = istio_tcp_received_response[0]['values']

        begin_timestamp, begin_traffic_sent_counter = values_sent[0]
        end_timestamp, end_traffic_sent_counter = values_sent[-1]
        begin_timestamp, begin_traffic_received_counter = values_received[0]
        end_timestamp, end_traffic_received_counter = values_received[-1]

        data_points_num_sent = len(values_sent)
        data_points_num_recevied = len(values_received)

        average_traffic_sent = (int(end_traffic_sent_counter) - int(begin_traffic_sent_counter)) / data_points_num_sent
        average_traffic_received = (int(end_traffic_received_counter) - int(begin_traffic_received_counter)) / data_points_num_recevied

        average_traffic_bytes = int((average_traffic_sent + average_traffic_received) / 2)
        print(f'from {workload_src} to {workload_dst} average_traffic_bytes: {int(average_traffic_bytes/1000)} KB' )
        return average_traffic_bytes
# Retrieve the list of ready deployments
_Namespace = 'social-network3'
ready_deployments = get_ready_deployments(_Namespace)

# Initialize an empty DataFrame for the exec_graph
df_exec_graph = pd.DataFrame(index=ready_deployments, columns=ready_deployments, data=0.0)


# Fill the DataFrame with average request values
for deployment_src in ready_deployments:
    for deployment_dst in ready_deployments:
        if deployment_src != deployment_dst:
            average_requests = transmitted_req_calculator(
                workload_src=deployment_src, 
                workload_dst=deployment_dst, 
                timerange=10,  # look back at the 10mins long history
                step_interval='1m', # window step in 1 miniute
                app_namespace = _Namespace
            )
            df_exec_graph.at[deployment_src, deployment_dst] = int(average_requests/1000) # calcuate KiloByte, instead of Byte

# Plot the heatmap for exec_graph
# plt.figure(figsize=(15, 12))
# sns.heatmap(df_exec_graph, cmap='viridis', fmt=".2f")
# plt.title('Average Requests per 5 Minutes among Pods')
# plt.xlabel('Destination Pods')
# plt.ylabel('Source Pods')
# plt.show()

# Convert DataFrame to exec_graph (numpy array)
exec_graph = df_exec_graph.to_numpy()




df_exec_graph.to_csv('df_exec_graph.csv')



deployment_node_dict = {}
deployment_list = ready_deployments
apps_v1 = client.AppsV1Api()


for deployment_name in deployment_list:
    try:
        # Get the deployment object
        deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace='social-network3')
        # Get the pod selector from the deployment
        pod_selector = deployment.spec.selector.match_labels

        # List all pods in the namespace
        pods = v1.list_namespaced_pod(_Namespace)

        # Find pods that match the deployment selector
        for pod in pods.items:
            if all(item in pod.metadata.labels.items() for item in pod_selector.items()):
                # Get the node name where the pod is running
                node_name = pod.spec.node_name
                # Assuming one pod per deployment for simplicity, can be expanded if needed
                deployment_node_dict[deployment_name] = node_name
                break  # Found the pod for this deployment, no need to continue

    except client.exceptions.ApiException as e:
        print(f"Exception when retrieving deployment {deployment_name}: {e}")




# return 
deployment_node_dict


def get_worker_node_numbers(deployment_node_dict):
    # Extract node numbers from the dictionary
    
    #the actual node number is like (node1, node2, node3, ...., node9)
    # node_numbers = [int(node.split('-')[-1]) for node in deployment_node_dict.values()] 
    
    # make the correspoding adjustment to (node0, node1, node2, ...,node8), otherwsie there will be index>=9 error in total_cost calculation
    node_numbers = [(int(node.split('-')[-1]) - 1) for node in deployment_node_dict.values()] 

    return node_numbers



'''get the cross-node delay matrix'''
import numpy as np
from kubernetes import stream
# Function to measure node-to-node latency
def measure_http_latency(namespace='measure-nodes'):
    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace, label_selector="app=latency-measurement").items
    latency_results = {}
    
    for source_pod in pods:
        source_pod_name = source_pod.metadata.name
        source_pod_node_name = source_pod.spec.node_name
        latency_results[source_pod_node_name] = {}
        
        for target_pod in pods:
            target_pod_ip = target_pod.status.pod_ip
            target_pod_name = target_pod.metadata.name
            target_pod_node_name = target_pod.spec.node_name
            if source_pod_name != target_pod_name:
                exec_command = ['curl', '-o', '/dev/null', '-s', '-w', '%{time_total}', f'http://{target_pod_ip}']
                try:
                    resp = stream.stream(v1.connect_get_namespaced_pod_exec,
                                         source_pod_name,
                                         namespace,
                                         command=exec_command,
                                         stderr=True,
                                         stdin=False,
                                         stdout=True,
                                         tty=False)
                    latency_results[source_pod_node_name][target_pod_node_name] = float(resp) * 1000
                except Exception as e:
                    print(f"Error executing command in pod {source_pod_name}: {e}")
                    latency_results[source_pod_node_name][target_pod_node_name] = np.inf  # Use infinity for errors
    
    return latency_results

# Call the function to measure latency
namespace = 'measure-nodes'
latency_results = measure_http_latency(namespace=namespace)


# Convert the nested dictionary into a pandas DataFrame and handle self-latency
df_latency = pd.DataFrame(latency_results).T
for worker in df_latency.columns:
    df_latency.at[worker, worker] = 0
    
# Convert DataFrame to delay matrix (numpy array)
delay_matrix = df_latency.to_numpy()
delay_matrix


'''microservice-node mapping placement'''

# Define the functions for placement and cost calculation
def calculate_communication_cost(exec_graph, placement, delay_matrix):
    cost = 0
    for u in range(len(exec_graph)):
        for v in range(len(exec_graph[u])):
            if exec_graph[u][v] > 0:
                server_u = placement[u]
                server_v = placement[v]
                cost += exec_graph[u][v] * delay_matrix[server_u][server_v]
    return cost

def greedy_placement_worker(exec_graph, delay_matrix, placement, num_servers, start, end):
    current_cost = calculate_communication_cost(exec_graph, placement, delay_matrix)
    improved = True
    while improved:
        improved = False
        for u in range(start, end):
            current_server = placement[u]
            for new_server in range(num_servers):
                if new_server != current_server:
                    new_placement = placement.copy()
                    new_placement[u] = new_server
                    new_cost = calculate_communication_cost(exec_graph, new_placement, delay_matrix)
                    if new_cost < current_cost:
                        placement = new_placement
                        current_cost = new_cost
                        improved = True
                        break
            if improved:
                break
    return placement, current_cost

# divides the placement optimization task into chunks and runs them in parallel using multiple worker processes.
def parallel_greedy_placement(exec_graph, delay_matrix, placement, num_servers, num_workers=4):
    num_microservices = len(exec_graph)
    chunk_size = (num_microservices + num_workers - 1) // num_workers  # Adjust chunk size to cover all microservices
    print(f"{chunk_size} = ({num_microservices} + {num_workers} - 1) // {num_workers}")

    while True:
        pool = mp.Pool(num_workers)
        chunks = [(exec_graph, delay_matrix, placement, num_servers, i*chunk_size, min((i+1)*chunk_size, num_microservices)) for i in range(num_workers)] #divides the placement optimization task into chunks
        results = pool.starmap(greedy_placement_worker, chunks) #distributes the chunks to the worker processes and collects their results
        pool.close() #prevents any more tasks from being submitted to the pool
        pool.join() #waits for all worker processes to finish

        # print("Chunks:", chunks)
        print("lengnths of results:", len(results))
        print("Results:", results)
        # Find the best result from all chunks
        new_placement = results[0][0] #initializes the best placement and cost with the first result
        new_cost = results[0][1] #initializes the best placement and cost with the first result
        improved = False

        for result in results[1:]:
            if result[1] < new_cost:
                new_placement = result[0]
                new_cost = result[1]
                improved = True

        if not improved:
            break

        placement = new_placement

    return placement, new_cost



# test usage with the generated delay matrix and initial placement
M = len(exec_graph)  # Number of microservices
N = len(delay_matrix)  # Number of servers

# Initial random placement
# placement = [random.randint(0, N - 1) for _ in range(M)]
initial_placement = get_worker_node_numbers(deployment_node_dict)


initial_cost = calculate_communication_cost(exec_graph, initial_placement, delay_matrix)

# Perform parallel greedy placement
final_placement, total_cost = parallel_greedy_placement(exec_graph, delay_matrix, initial_placement, N, num_workers=mp.cpu_count())

print("innitial_placement:", initial_placement)
print("initial_cost:", initial_cost)
print("Final Placement:", final_placement)
print("Total Communication Cost:", total_cost)


# compare the initial and final placement, find the migrations needed
def migrate_microservices(initial_placement, final_placement):
    migrations = []
    for microservice, (initial, final) in enumerate(zip(initial_placement, final_placement)):
        if initial != final:
            migrations.append((microservice, initial, final))
    return migrations

def exclude_non_App_ms(migrations, microservice_names, exclude_deployments=['jager']):
    excluded_indices = {index for index, name in enumerate(microservice_names) if name in exclude_deployments}
    return [(ms, initial, final) for ms, initial, final in migrations if ms not in excluded_indices]



# Avoid migrating non-application deployments like 'jager' and 'prometheus'
exclude_deployments = ['jaeger']
microservice_names = ready_deployments

migrations = migrate_microservices(initial_placement, final_placement)
filtered_migrations = exclude_non_App_ms(migrations, microservice_names, exclude_deployments)




from kubernetes import client, config
import time

# Load the kube config from the default location
config.load_kube_config()

# API instances
apps_v1_api = client.AppsV1Api()
core_v1_api = client.CoreV1Api()


def patch_deployment(deployment_name, namespace, new_node_name):
    """Patch the deployment to use a specific node."""
    body = {
        "spec": {
            "template": {
                "spec": {
                    "nodeSelector": {
                        "kubernetes.io/hostname": new_node_name
                    }
                }
            }
        }
    }
    try:
        apps_v1_api.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=body)
        print(f"Deployment '{deployment_name}' patched to schedule pods on '{new_node_name}'.")
    except Exception as e:
        print(f"Failed to patch the deployment: {e}")
        return False
    return True

def wait_for_rolling_update_to_complete(deployment_name, namespace, new_node_name):
    """Wait for the rolling update to complete."""
    print("Waiting for the rolling update to complete...")
    while True:
        pods = core_v1_api.list_namespaced_pod(namespace=namespace, label_selector=f'app={deployment_name}').items
        all_pods_updated = all(pod.spec.node_name == new_node_name and
                               pod.status.phase == 'Running'
                               for pod in pods)
        print("all_pods_updated=",all_pods_updated)
        print("len(pods)=", len(pods))
        if all_pods_updated and len(pods) >= 0:
            print("All pods are running on the new node.")
            break
        else:
            print("Rolling update in progress...")
            time.sleep(5)



print("Migrations needed:")
for microservice, initial, final in filtered_migrations: # iterate over the filtered migrations
    print(f"Microservice {microservice} from Node {initial} to Node {final}")
    print(f"Microservice {ready_deployments[microservice]} from Node {initial+1} to Node {final+1}")
    if patch_deployment(ready_deployments[microservice], _Namespace, node_name='k8s-worker-' + str(final + 1)):
        wait_for_rolling_update_to_complete(ready_deployments[microservice], _Namespace, new_node_name='k8s-worker-' + str(final + 1))
        print(f"Microservice {ready_deployments[microservice]} migrated successfully.")

