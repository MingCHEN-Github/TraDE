#!/bin/bash

# Ming Chen, 25 July

# editing sending requests for bookinfo microservice app

# Getting the Gateway Url
export INGRESS_PORT=$( kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
export SECURE_INGRESS_PORT=$( kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')

export INGRESS_HOST=$( kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath='{.items[0].status.hostIP}')

export GATEWAY_URL=$INGRESS_HOST:$INGRESS_PORT



#!/bin/bash

#!/bin/bash

#!/bin/bash

GATEWAY_URL=GATEWAY_URL

SLEEP_TIME=0.1
TOTAL_REQUESTS=50000

# Create an associative array
declare -A user_count=( ["user1_cookie.txt"]=0 ["user2_cookie.txt"]=0 ["user3_cookie.txt"]=0 ["user4_cookie.txt"]=0 ["user5_cookie.txt"]=0 )

echo "Starting script at $(date)"

# Create cookie files
touch user1_cookie.txt user2_cookie.txt user3_cookie.txt user4_cookie.txt user5_cookie.txt

for i in $(seq 1 $TOTAL_REQUESTS)
do
    # Generate a random number between 1 and 5
    user_num=$(( $RANDOM % 5 + 1 ))
    user_cookie="user${user_num}_cookie.txt"

    curl -s -o /dev/null -b $user_cookie -c $user_cookie "http://$GATEWAY_URL/productpage"

    # Increase the count for the selected user
    user_count[$user_cookie]=$(( ${user_count[$user_cookie]} + 1 ))

    if [ $(($i % 200)) -eq 0 ]; then
        echo "Sent $i requests so far by user: $user_cookie..."
        sleep $SLEEP_TIME
    fi
done

echo "Script finished at $(date)"

# Print out the final count for each user
echo "Final count of requests per user:"
for user in "${!user_count[@]}"
do
    echo "$user: ${user_count[$user]}"
done
