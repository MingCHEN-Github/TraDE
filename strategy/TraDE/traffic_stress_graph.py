'''Building traffic Stress graph, return the ms execution graph with bi-direction traffic '''
import pandas as pd
from datetime import datetime, timedelta

# Function to retrieve ready deployments
# def get_ready_deployments(namespace):
#     ready_deployments = []
#     deployments = client.AppsV1Api().list_namespaced_deployment(namespace)
#     for deployment in deployments.items:
#         if deployment.status.ready_replicas == deployment.spec.replicas:
#             ready_deployments.append(deployment.metadata.name)
#     return ready_deployments

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
