#!/bin/bash

#Ming Chen, 25 July, 2023
# editing sending requests for bookinfo microservice app

# Getting the Gateway Url
export INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="http2")].nodePort}')
export SECURE_INGRESS_PORT=$(kubectl -n istio-system get service istio-ingressgateway -o jsonpath='{.spec.ports[?(@.name=="https")].nodePort}')

export INGRESS_HOST=$(kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath='{.items[0].status.hostIP}')

export GATEWAY_URL=$INGRESS_HOST:$INGRESS_PORT



#!/bin/bash
#  sending  requests   with  every 100 requests and sleep for  0.1 seconds


echo ${GATEWAY_URL}
