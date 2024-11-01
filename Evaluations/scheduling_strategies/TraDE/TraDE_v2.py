'''modified version of TraDE_v2.py in a  more readable format'''

import stat
from kubernetes import client, config, stream
import pandas as pd
from prometheus_api_client import PrometheusConnect
from datetime import datetime, timedelta
import numpy as np
import random
import multiprocessing as mp
import time

class TraDE_MicroserviceScheduler:
    def __init__(self, prom_url, qos_target, time_window, namespace, response_code='200'):
        # Kubernetes Config
        config.load_kube_config()
        self.v1 = client.CoreV1Api()

        # Prometheus Config
        self.prom = PrometheusConnect(url=prom_url, disable_ssl=True)
        self.qos_target = qos_target
        self.time_window = time_window
        self.namespace = namespace
        self.response_code = response_code

        # Test Prometheus connection
        prom_connect_response = self.prom.custom_query(query="up")
        print(prom_connect_response)

    def trigger_migration(self):
        """
        Determine if migration should be triggered based on QoS target and time window.
        """
        trigger = False
        step = str(self.time_window * 60)  # Step size in seconds for Prometheus queries

        # Prometheus queries for Istio metrics
        istio_request_duration_query = f'rate(istio_request_duration_milliseconds_sum{{namespace="{self.namespace}", response_code="{self.response_code}"}}[{self.time_window}m])'
        istio_requests_total_query = f'rate(istio_requests_total{{namespace="{self.namespace}", response_code="{self.response_code}"}}[{self.time_window}m])'

        # Define the time range for the query
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=self.time_window)

        # Fetch the data from Prometheus
        istio_request_duration_response = self.prom.custom_query_range(
            query=istio_request_duration_query,
            start_time=start_time,
            end_time=end_time,
            step=step
        )
        istio_requests_total_response = self.prom.custom_query_range(
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
                    if average_response_time > self.qos_target:
                        trigger = True
                else:
                    print("Total requests sum is zero, cannot compute average response time.")
            else:
                print("No traffic detected, no trigger.")
        else:
            print("Query returned no data, no trigger.")

        print(f"Trigger = {trigger}")

        return trigger

    def get_ready_deployments(self):
        """
        Retrieve ready deployments in a namespace.
        """
        ready_deployments = []
        deployments = client.AppsV1Api().list_namespaced_deployment(self.namespace)
        for deployment in deployments.items:
            if deployment.status.ready_replicas == deployment.spec.replicas:
                ready_deployments.append(deployment.metadata.name)
        return ready_deployments

    def transmitted_req_calculator(self, workload_src, workload_dst, timerange, step_interval):
        """
        Calculate transmitted requests between source and destination workloads.
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=timerange)

        istio_tcp_sent_query = f'istio_tcp_sent_bytes_total{{reporter="source",source_workload="{workload_src}",destination_workload="{workload_dst}", namespace = "{self.namespace}"}}'
        istio_tcp_received_query = f'istio_tcp_received_bytes_total{{reporter="source",source_workload="{workload_src}",destination_workload="{workload_dst}", namespace = "{self.namespace}"}}'

        istio_tcp_sent_response = self.prom.custom_query_range(
            query=istio_tcp_sent_query,
            start_time=start_time,
            end_time=end_time,
            step=step_interval
        )
        istio_tcp_received_response = self.prom.custom_query_range(
            query=istio_tcp_received_query,
            start_time=start_time,
            end_time=end_time,
            step=step_interval
        )

        if (not istio_tcp_sent_response or not istio_tcp_sent_response[0]['values']) and (not istio_tcp_received_response or not istio_tcp_received_response[0]['values']):
            return 0
        else:
            values_sent = istio_tcp_sent_response[0]['values']
            values_received = istio_tcp_received_response[0]['values']

            begin_timestamp, begin_traffic_sent_counter = values_sent[0]
            end_timestamp, end_traffic_sent_counter = values_sent[-1]
            begin_timestamp, begin_traffic_received_counter = values_received[0]
            end_timestamp, end_traffic_received_counter = values_received[-1]

            data_points_num_sent = len(values_sent)
            data_points_num_received = len(values_received)

            average_traffic_sent = (int(end_traffic_sent_counter) - int(begin_traffic_sent_counter)) / data_points_num_sent
            average_traffic_received = (int(end_traffic_received_counter) - int(begin_traffic_received_counter)) / data_points_num_received

            average_traffic_bytes = int((average_traffic_sent + average_traffic_received) / 2)
            print(f'from {workload_src} to {workload_dst} average_traffic_bytes: {int(average_traffic_bytes/1000)} KB')
            return int(average_traffic_bytes/1000) # covert Byte to KB

    def build_exec_graph(self):
        """
        Build the execution graph based on average request values between deployments.
        """
        ready_deployments = self.get_ready_deployments()
        df_exec_graph = pd.DataFrame(index=ready_deployments, columns=ready_deployments, data=0.0)

        for deployment_src in ready_deployments:
            for deployment_dst in ready_deployments:
                if deployment_src != deployment_dst:
                    average_requests = self.transmitted_req_calculator(
                        workload_src=deployment_src,
                        workload_dst=deployment_dst,
                        timerange=10,
                        step_interval='1m'
                    )
                    df_exec_graph.at[deployment_src, deployment_dst] = int(average_requests / 1000)

        df_exec_graph.to_csv('df_exec_graph.csv')
        return df_exec_graph.to_numpy(), ready_deployments

    def get_deployment_node_dict(self, deployment_list):
        """
        Get a dictionary mapping deployments to nodes.
        """
        deployment_node_dict = {}
        apps_v1 = client.AppsV1Api()

        for deployment_name in deployment_list:
            try:
                deployment = apps_v1.read_namespaced_deployment(deployment_name, namespace=self.namespace)
                pod_selector = deployment.spec.selector.match_labels
                pods = self.v1.list_namespaced_pod(self.namespace)

                for pod in pods.items:
                    if all(item in pod.metadata.labels.items() for item in pod_selector.items()):
                        node_name = pod.spec.node_name
                        deployment_node_dict[deployment_name] = node_name
                        break

            except client.exceptions.ApiException as e:
                print(f"Exception when retrieving deployment {deployment_name}: {e}")

        return deployment_node_dict

    def get_worker_node_numbers(self, deployment_node_dict):
        """
        Extract node numbers from the dictionary.
        """
        return [(int(node.split('-')[-1]) - 1) for node in deployment_node_dict.values()]

    def measure_http_latency(self, namespace='measure-nodes'):
        """
        Measure node-to-node latency using HTTP requests.
        """
        pods = self.v1.list_namespaced_pod(namespace, label_selector="app=latency-measurement").items
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
                        resp = stream.stream(self.v1.connect_get_namespaced_pod_exec,
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
                        latency_results[source_pod_node_name][target_pod_node_name] = np.inf

        df_latency = pd.DataFrame(latency_results).T
        for worker in df_latency.columns:
            df_latency.at[worker, worker] = 0

        return df_latency.to_numpy()

    @staticmethod
    def calculate_communication_cost(exec_graph, placement, delay_matrix):
        """
        Calculate the communication cost based on the exec graph and delay matrix.
        """
        cost = 0
        for u in range(len(exec_graph)):
            for v in range(len(exec_graph[u])):
                if exec_graph[u][v] > 0:
                    server_u = placement[u]
                    server_v = placement[v]
                    cost += exec_graph[u][v] * delay_matrix[server_u][server_v]
        return cost
    
    @staticmethod
    def greedy_placement_worker(exec_graph, delay_matrix, placement, num_servers, start, end):
        """
        Perform a greedy placement optimization for a chunk of microservices.
        """
        current_cost = TraDE_MicroserviceScheduler.calculate_communication_cost(exec_graph, placement, delay_matrix)
        improved = True
        while improved:
            improved = False
            for u in range(start, end):
                current_server = placement[u]
                for new_server in range(num_servers):
                    if new_server != current_server:
                        new_placement = placement.copy()
                        new_placement[u] = new_server
                        new_cost = TraDE_MicroserviceScheduler.calculate_communication_cost(exec_graph, new_placement, delay_matrix)
                        if new_cost < current_cost:
                            placement = new_placement
                            current_cost = new_cost
                            improved = True
                            break
                if improved:
                    break
        return placement, current_cost
    
    @staticmethod
    def parallel_greedy_placement(exec_graph, delay_matrix, placement, num_servers, num_workers=4): # remove 'self' when using @staticmethod
        """
        Perform parallel greedy placement optimization.
        """
        num_microservices = len(exec_graph)
        chunk_size = (num_microservices + num_workers - 1) // num_workers
        print(f"{chunk_size} = ({num_microservices} + {num_workers} - 1) // {num_workers}")

        while True:
            pool = mp.Pool(num_workers)
            chunks = [(exec_graph, delay_matrix, placement, num_servers, i * chunk_size, min((i + 1) * chunk_size, num_microservices)) for i in range(num_workers)]
            results = pool.starmap(TraDE_MicroserviceScheduler.greedy_placement_worker, chunks)
            pool.close()
            pool.join()

            new_placement = results[0][0]
            new_cost = results[0][1]
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

    def migrate_microservices(self, initial_placement, final_placement):
        """
        Determine the required migrations based on initial and final placements.
        """
        migrations = []
        for microservice, (initial, final) in enumerate(zip(initial_placement, final_placement)):
            if initial != final:
                migrations.append((microservice, initial, final))
        return migrations

    def exclude_non_App_ms(self, migrations, microservice_names, exclude_deployments=['jager']):
        """
        Exclude non-application microservices from the migration list.
        """
        excluded_indices = {index for index, name in enumerate(microservice_names) if name in exclude_deployments}
        return [(ms, initial, final) for ms, initial, final in migrations if ms not in excluded_indices]

    def patch_deployment(self, deployment_name, new_node_name):
        """
        Patch the deployment to use a specific node.
        """
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
            client.AppsV1Api().patch_namespaced_deployment(name=deployment_name, namespace=self.namespace, body=body)
            print(f"Deployment '{deployment_name}' patched to schedule pods on '{new_node_name}'.")
        except Exception as e:
            print(f"Failed to patch the deployment: {e}")
            return False
        return True

    def wait_for_rolling_update_to_complete(self, deployment_name, new_node_name):
        """
        Wait for the rolling update to complete.
        """
        print("Waiting for the rolling update to complete...")
        while True:
            pods = client.CoreV1Api().list_namespaced_pod(namespace=self.namespace, label_selector=f'app={deployment_name}').items
            all_pods_updated = all(pod.spec.node_name == new_node_name and pod.status.phase == 'Running' for pod in pods)
            print("all_pods_updated=", all_pods_updated)
            print("len(pods)=", len(pods))
            if all_pods_updated and len(pods) >= 0:
                print("All pods are running on the new node.")
                break
            else:
                print("Rolling update in progress...")
                time.sleep(5)

    def run(self):
        """
        Main function to run the scheduler.
        """
        print("Running the scheduler...:", datetime.now())
        # Trigger migration if needed
        if self.trigger_migration():
            # Build the execution graph
            exec_graph, ready_deployments = self.build_exec_graph()

            # Get the initial deployment node mapping
            deployment_node_dict = self.get_deployment_node_dict(ready_deployments)
            initial_placement = self.get_worker_node_numbers(deployment_node_dict)

            # Measure node-to-node latency
            delay_matrix = self.measure_http_latency()

            # Calculate the initial communication cost
            initial_cost = self.calculate_communication_cost(exec_graph, initial_placement, delay_matrix)
            print("Initial Placement:", initial_placement)
            print("Initial Communication Cost:", initial_cost)

            # Perform parallel greedy placement
            final_placement, total_cost = self.parallel_greedy_placement(exec_graph, delay_matrix, initial_placement, len(delay_matrix), num_workers=mp.cpu_count())
            print("Final Placement:", final_placement)
            print("Total Communication Cost:", total_cost)

            # Determine required migrations
            migrations = self.migrate_microservices(initial_placement, final_placement)
            filtered_migrations = self.exclude_non_App_ms(migrations, ready_deployments, exclude_deployments=['jaeger'])
            print("Migrations needed:")
            for microservice, initial, final in filtered_migrations:
                print(f"Microservice {microservice} from Node {initial} to Node {final}")
                print(f"Microservice {ready_deployments[microservice]} from Node {initial + 1} to Node {final + 1}")
                if self.patch_deployment(ready_deployments[microservice], new_node_name='k8s-worker-' + str(final + 1)):
                    self.wait_for_rolling_update_to_complete(ready_deployments[microservice], new_node_name='k8s-worker-' + str(final + 1))
                    print(f"Microservice {ready_deployments[microservice]} migrated successfully.")
        else:
            print("No migration needed.")



if __name__ == "__main__":
    # Initialize the scheduler with necessary parameters
    prom_url = "http://10.105.116.175:9090"
    qos_target = 300  # QoS target in milliseconds
    # time_window is the look_back window for the average response time
    time_window = 2  # Time window in minutes,
    namespace = 'social-network3'
    response_code = '200'  # HTTP response code to consider

    # Create an instance of the scheduler
    scheduler = TraDE_MicroserviceScheduler(prom_url, qos_target, time_window, namespace, response_code)

    # Run the scheduler
    while True:
        scheduler.run()
        time.sleep(10)
    # scheduler.run()
