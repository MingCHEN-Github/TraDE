'''
(1) check all pods of the deployed Application (bookInfo) are ready and running
'''
# Function: check ready state for all the pods in given namespace
from kubernetes import client, config
from traitlets import default

def are_all_pods_ready(namespace):
    config.load_kube_config()  # Use load_incluster_config() if running inside a pod

    # Create an instance of the API class
    v1 = client.CoreV1Api()
    try:
        # List all Pods in the specified namespace
        pods = v1.list_namespaced_pod(namespace)
        
        for pod in pods.items:
            # Check if the pod status is not 'Running' or if any of the containers are not ready
            if pod.status.phase != 'Running' or not all(container.ready for container in pod.status.container_statuses):
                return False  # Return False if any pod is not ready
        
        return True  # Return True if all pods are ready
    except Exception as e:
        print(f"An error occurred: {e}")
        return False  # Return False in case of any error during API call
    
'''
(2) get the inital deployement of pods (bind in which node)
'''    
#Function: get all pod initial placement and save 

import pandas as pd
from pod_placement import get_initial_pod_placement

get_initial_pod_placement.save_pod_placement_to_csv(namespace=default)

initial_placement = pd.read_csv('/home/ubuntu/ms_scheduling/book_info/pod_placement/initial_pod_placement_bookinfo_v2.csv')
initial_pod_placement = {'review-v1':'k8s-worker-'}


# 


# running test with different pod placements 
# a) initial placements;
# b) descheduling pod placements;
# c) write a loop with different reqests sending (2k req, 5k req, and 10k req, etc.)




#