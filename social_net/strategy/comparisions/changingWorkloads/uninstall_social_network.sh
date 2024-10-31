#!/bin/bash

# Uninstall the social network helm charts from the cluster

# $ chmod +x uninstall_social_network.sh
# $ ./uninstall_social_network.sh

# Define variables
RELEASE_NAMES=("social-net1" "social-net2" "social-net3")
NAMESPACES=("social-network" "social-network2" "social-network3")

# Loop through each release name and namespace to uninstall the helm charts
for i in ${!RELEASE_NAMES[@]}; do
  RELEASE_NAME=${RELEASE_NAMES[$i]}
  NAMESPACE=${NAMESPACES[$i]}
  
  # Execute the helm uninstall command
  helm uninstall "$RELEASE_NAME" --namespace "$NAMESPACE"
  
  # Output the result of the command
  if [ $? -eq 0 ]; then
    echo "Helm release $RELEASE_NAME uninstalled successfully from namespace $NAMESPACE."
  else
    echo "Failed to uninstall $RELEASE_NAME from namespace $NAMESPACE." >&2
  fi
done
