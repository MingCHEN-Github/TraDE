#!/bin/bash

#Ming Chen, 25 July,2023
# editing sending requests for bookinfo microservice app

# Getting the Gateway Url
export INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
export SECURE_INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')

export INGRESS_HOST=$(kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath='{.items[0].status.hostIP}')

export GATEWAY_URL=$INGRESS_HOST:$INGRESS_PORT



#!/bin/bash
#  sending  requests   with  every 100 requests and sleep for  0.1 seconds
#GATEWAY_URL=your_gateway_url

echo "Starting script at $(date)"

for i in $(seq 1 100)
do
    curl -s -o /dev/null -w "%{http_code} in %{time_total}s\n" "http://$GATEWAY_URL/productpage"
    
    if [ $(($i % 1)) -eq 0 ]; then
        echo "Sent $i requests so far..."
        sleep 0
    fi
done

echo "Script finished at $(date)"