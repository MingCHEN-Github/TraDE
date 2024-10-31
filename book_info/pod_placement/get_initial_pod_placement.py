from kubernetes import client, config
import csv
import os

# Load kube config
config.load_kube_config()

# Define the namespace to fetch pods from
namespace = 'default'  # Change this to the desired namespace

# API instance
v1 = client.CoreV1Api()

def get_deployment_name_from_pod(pod):
    """
    Attempts to derive the deployment name from a pod's owner references.
    Looks for a ReplicaSet owner and assumes the deployment name can be inferred from it.
    """
    for owner in pod.metadata.owner_references:
        if owner.kind == "ReplicaSet":
            # Try to remove the generated suffix from the ReplicaSet name
            # Assuming the ReplicaSet name format is: [deployment-name]-[random-hash]
            # this can be checked at Pod's owner_references field
            return owner.name.rsplit('-', 1)[0]
    return "Unknown"

def save_pod_placement_to_csv(namespace):
    file_name = '/home/ubuntu/ms_scheduling/book_info/pod_placement/initial_pod_placement_bookinfo_v2.csv'
    # Fetch all pods in the specified namespace
    pods = v1.list_namespaced_pod(namespace)

    # Open a file to write
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        # Write the header
        writer.writerow(['Deployment Name', 'Pod Name', 'Host Node', 'IP Address'])

        # Loop through each pod and write its properties
        for pod in pods.items:
            deployment_name = get_deployment_name_from_pod(pod)
            pod_name = pod.metadata.name
            node_name = pod.spec.node_name
            ip_address = pod.status.pod_ip
            writer.writerow([deployment_name, pod_name, node_name, ip_address])

    full_path = os.path.join(os.getcwd(), file_name)
    print(f"Pod placements have been saved to {full_path}")

# Call the function
save_pod_placement_to_csv(namespace)
