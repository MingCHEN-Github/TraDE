#!/bin/bash

# $ chmod +x install_social_network.sh
# $ ./install_social_network.sh


# Define variables
HELM_CHART_REPO_PATH=~/DeathStarBench/socialNetwork/helm-chart/socialnetwork
RELEASE_NAMES=("social-net1" "social-net2" "social-net3")
NAMESPACES=("social-network" "social-network2" "social-network3")
MEMORY_REQUEST="64Mi"
CPU_REQUEST="150m"
MEMORY_LIMIT="256Mi"
CPU_LIMIT="300m"
COMPOSE_MEMORY_REQUEST="64Mi"
COMPOSE_CPU_REQUEST="300m"
COMPOSE_MEMORY_LIMIT="256Mi"
COMPOSE_CPU_LIMIT="500m"

# Loop through each release name and namespace to install the helm charts
for i in ${!RELEASE_NAMES[@]}; do
  RELEASE_NAME=${RELEASE_NAMES[$i]}
  NAMESPACE=${NAMESPACES[$i]}
  
  # Execute the helm install command
  helm install "$RELEASE_NAME" "$HELM_CHART_REPO_PATH" \
  --namespace "$NAMESPACE" \
  --set global.resources.requests.memory="$MEMORY_REQUEST" \
  --set global.resources.requests.cpu="$CPU_REQUEST" \
  --set global.resources.limits.memory="$MEMORY_LIMIT" \
  --set global.resources.limits.cpu="$CPU_LIMIT" \
  --set compose-post-service.container.resources.requests.memory="$COMPOSE_MEMORY_REQUEST" \
  --set compose-post-service.container.resources.requests.cpu="$COMPOSE_CPU_REQUEST" \
  --set compose-post-service.container.resources.limits.memory="$COMPOSE_MEMORY_LIMIT" \
  --set compose-post-service.container.resources.limits.cpu="$COMPOSE_CPU_LIMIT"
  
  # Output the result of the command
  if [ $? -eq 0 ]; then
    echo "Helm release $RELEASE_NAME installed successfully in namespace $NAMESPACE."
  else
    echo "Failed to install $RELEASE_NAME in namespace $NAMESPACE." >&2
  fi
done
