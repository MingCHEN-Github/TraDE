from os import getenv
from json import loads as json_loads
import random

from kubernetes import config, watch
from kubernetes.client import ApiClient, CoreV1Api, V1ObjectReference, V1ObjectMeta, V1Binding, Configuration
from kubernetes.client.rest import ApiException, RESTClientObject

from logging import basicConfig, getLogger, INFO

from kubernetes import client, config, watch
# import pandas as pd
# import matplotlib.pyplot as plt

# from prometheus_api_client import PrometheusConnect

# from datetime import datetime, timedelta
# import time
# from difflib import diff_bytes
# import matplotlib.pyplot as plt
# import kubernetes.client.models.v1_pod as v1pod

formatter = " %(asctime)s | %(levelname)-6s | %(process)d | %(threadName)-12s |" \
            " %(thread)-15d | %(name)-30s | %(filename)s:%(lineno)d | %(message)s |"
basicConfig(level=INFO, format=formatter)
logger = getLogger("meetup-scheduler")

V1_CLIENT = None  # type: CoreV1Api
SCHEDULE_STRATEGY = "schedulingStrategy=meetup"
_NOSCHEDULE_TAINT = "NoSchedule"



import requests


def find_loweset_bandwidth(): 
    # URL of your Prometheus server
    # PROMETHEUS = "http://prometheus-stack-kube-prom-prometheus.monitoring.svc.cluster.local:9090"
    PROMETHEUS= "http://10.110.188.57:9090"
    query = 'instance:node_network_receive_bytes:rate:sum'
    url = f'{PROMETHEUS}/api/v1/query'

    # Parameters for the query
    params = {
        'query': query,
        # Optionally, can be specified the exact time to query for
        # 'time': '2024-02-27T12:00:00Z',
    }
     # Make the HTTP GET request
    response = requests.get(url, params=params)
    
    print("************111**********response.status_code===",response.status_code)
    node_bandwidth = {}
    
    # Check if the request was successful
    if response.status_code == 200:
        result = response.json()
        # Extract and print just the result data
        data = result.get('data', {}).get('result', [])
        if data:
            for item in data:
                # Assuming the query returns vector results, iterate and print
                metric_name = item.get('metric', {}).get('__name__', 'Unknown metric')
                instance_name = item.get('metric', {}).get('instance', 'Unknown instance')
                value = item.get('value', [])[1]  # The value is a [timestamp, value] pair
                # print(f'node {instance_name} has network bandith with :{value}')
                # save the instance name and value to a dictionary
                instance_ip = instance_name.split(":")[0] # get the ip of the instance, Eg: change this string "172.26.128.228:9100'" into "172.26.128.228"
                node_bandwidth[instance_ip] = float(value) # change string value into float
        else:
            print("No data returned")
    else:
        print(f"Failed to retrieve data: {response.status_code} - {response.text}")
    # print(node_bandwidth)
    
    
    lowest_bandwidth = node_bandwidth[list(node_bandwidth.keys())[0]]
    logger.info(f"******222*******lowest_bandwidth==={lowest_bandwidth}")
    lowest_bandwidth_node = None
    for node, bandwidth in node_bandwidth.items():
        if bandwidth < lowest_bandwidth:
            lowest_bandwidth = bandwidth
            lowest_bandwidth_node = node
        logger.info(f"******333*******lowest_bandwidth==={lowest_bandwidth_node}")
        
    return lowest_bandwidth_node, lowest_bandwidth

#find the node name with lowest bandwidth
# lowest_bandwidth_node, lowest_bandwidth = find_loweset_bandwidth(node_bandwidth)
# print(f"the node with lowest bandwidth is {lowest_bandwidth_node} with bandwidth {lowest_bandwidth}")



def _get_ready_nodes(v1_client, filtered=True):
    ready_nodes = []
    try:
        for n in v1_client.list_node().items:
            if n.metadata.labels.get("noCustomScheduler") == "yes":
                logger.info(f"Skipping Node {n.metadata.name} since it has noCustomScheduler label")
                continue
            if filtered:
                if not n.spec.unschedulable:
                    no_schedule_taint = False
                    if n.spec.taints:
                        for taint in n.spec.taints:
                            if _NOSCHEDULE_TAINT == taint.to_dict().get("effect", None):
                                no_schedule_taint = True
                                break
                    if not no_schedule_taint:
                        for status in n.status.conditions:
                            if status.status == "True" and status.type == "Ready" and n.metadata.name:
                                ready_nodes.append(n.metadata.name)
                    else:
                        logger.error("NoSchedule taint effect on node %s", n.metadata.name)
                else:
                    logger.error("Scheduling disabled on %s ", n.metadata.name)
            else:
                if n.metadata.name:
                    ready_nodes.append(n.metadata.name)
        logger.info("Nodes : %s, Filtered: %s", ready_nodes, filtered)
    except ApiException as e:
        logger.error(json_loads(e.body)["message"])
        ready_nodes = []
    return ready_nodes

# later add the funtcion for choosing the node from schedulable nodes


def _get_schedulable_node(v1_client):
    pod_binding_node = None # Initialize pod_binding_node
    node_list = _get_ready_nodes(v1_client)
    if not node_list:
        return None
    available_nodes = list(set(node_list))
    # return random.choice(available_nodes) # later add the logic for choosing the node from the list of available nodes

        # find all nodes and its ip in the cluster, store the nodename and ip in a dictionary
    # config.load_kube_config()
    # config.load_incluster_config()
    # v1 = v1_client.CoreV1Api()
    node_ip = {}
    nodes = v1_client.list_node()
    # logger.info(f"*********444*******nodes={nodes}") #too long, all information have listed
    for node in nodes.items:
        for address in node.status.addresses:
            if address.type == "InternalIP":
                node_ip[node.metadata.name] = address.address
    print("node_ip=",node_ip)
    a, b =find_loweset_bandwidth()
    logger.info(f"*********444*******the node with lowest bandwidth is {a} with bandwidth {b}")
    # find the nodename based on the ip
    for node, ip in node_ip.items():
        if ip == a:
            pod_binding_node = node
            return pod_binding_node # return the node name with lowest bandwidth


def schedule_pod(v1_client, name, node, namespace="default"):
    target = V1ObjectReference()
    target.kind = "Node"
    target.apiVersion = "v1"
    target.name = node
    meta = V1ObjectMeta()
    meta.name = name
    body = V1Binding(api_version=None, kind=None, metadata=meta, target=target)
    logger.info("Binding Pod: %s  to  Node: %s", name, node)
    return v1_client.create_namespaced_pod_binding(name, namespace, body)

def watch_pod_events():
    V1_CLIENT = CoreV1Api()
    while True:
        try:
            logger.info("Checking for pod events....")
            try:
                watcher = watch.Watch()
                for event in watcher.stream(V1_CLIENT.list_pod_for_all_namespaces, label_selector=SCHEDULE_STRATEGY, timeout_seconds=20):
                    logger.info(f"Event: {event['type']} {event['object'].kind}, {event['object'].metadata.namespace}, {event['object'].metadata.name}, {event['object'].status.phase}")
                    if event["object"].status.phase == "Pending":
                        try:
                            logger.info(f'{event["object"].metadata.name} needs scheduling...')
                            pod_namespace = event["object"].metadata.namespace
                            pod_name = event["object"].metadata.name
                            service_name = event["object"].metadata.labels["serviceName"]
                            logger.info("Processing for Pod: %s/%s", pod_namespace, pod_name)
                            node_name = _get_schedulable_node(V1_CLIENT)
                            if node_name is not None: #Check if pod_binding_node is None before using it,This prevents errors when pod_binding_node is not assigned a value.
                                logger.info("Namespace %s, PodName %s , Node Name: %s  Service Name: %s",
                                            pod_namespace, pod_name, node_name, service_name)
                                res = schedule_pod(V1_CLIENT, pod_name, node_name, pod_namespace)
                                logger.info("Response %s ", res)
                            else:
                                logger.error(f"Found no valid node to schedule {pod_name} in {pod_namespace}")
                        except ApiException as e:
                            logger.error(json_loads(e.body)["message"])
                        except ValueError as e:
                            logger.error("Value Error %s", e)
                        except:
                            logger.exception("Ignoring Exception")
                logger.info("Resetting k8s watcher...")
            except:
                logger.exception("Ignoring Exception")
            finally:
                del watcher
        except:
            logger.exception("Ignoring Exception & listening for pod events")

def main():
    logger.info("Initializing the meetup scheduler...")
    logger.info("Watching for pod events...")
    watch_pod_events()


if __name__ == "__main__":
    config.load_incluster_config()
    main()