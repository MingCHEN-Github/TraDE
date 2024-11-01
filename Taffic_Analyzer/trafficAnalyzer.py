
import stat
from kubernetes import client, config, stream
import pandas as pd
from prometheus_api_client import PrometheusConnect
from datetime import datetime, timedelta
import numpy as np
import random
import multiprocessing as mp
import time
import concurrent.futures


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
            average_traffic_KB = int(average_traffic_bytes / 1000) # covert Byte to KB
            return average_traffic_KB  

def build_exec_graph(self):
        """
        Build the execution graph based on average request values between deployments.
        """
        ready_deployments = self.get_ready_deployments()
        df_exec_graph = pd.DataFrame(index=ready_deployments, columns=ready_deployments, data=0.0) # data=0.0 sets the initial value for all the cells in the DataFrame

        for deployment_src in ready_deployments:
            for deployment_dst in ready_deployments:
                if deployment_src != deployment_dst:
                    average_traffic_KB = self.transmitted_req_calculator(
                        workload_src=deployment_src,
                        workload_dst=deployment_dst,
                        timerange= 10, # look back window for the average response time
                        step_interval='1m'
                    )
                    df_exec_graph.at[deployment_src, deployment_dst] = average_traffic_KB

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

    
# Sort microservice pairs by traffic volume (for granular parallelism)
@staticmethod
def sort_microservice_pairs(exec_graph):
        """
        Sort the microservice pairs by traffic volume in descending order.
        
        Args:
            exec_graph: Traffic volume matrix between microservices.
        
        Returns:
            A sorted list of microservice pairs by traffic volume.
        """
        pairs = []
        for u in range(len(exec_graph)):
            for v in range(len(exec_graph[u])):
                if exec_graph[u][v] > 0:
                    pairs.append((u, v, exec_graph[u][v]))  # (source, destination, traffic volume)
        # Sort pairs by traffic volume in descending order
        pairs.sort(key=lambda x: -x[2])
        print("Sorted pairs:", pairs)
        return pairs