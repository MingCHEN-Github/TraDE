#!/usr/bin/env python3

import os
import requests
import time
from numpy import random

# Ming Chen, 25 July
# editing sending requests for bookinfo microservice app

# Getting the Gateway Url
INGRESS_PORT = os.popen(
    "kubectl -n istio-system get service istio-ingressgateway -o jsonpath=\"{.spec.ports[?(@.name=='http2')].nodePort}\""
).read()
SECURE_INGRESS_PORT = os.popen(
    "kubectl -n istio-system get service istio-ingressgateway -o jsonpath=\"{.spec.ports[?(@.name=='https')].nodePort}\""
).read()

INGRESS_HOST = os.popen(
    'kubectl get po -l istio=ingressgateway -n istio-system -o jsonpath="{.items[0].status.hostIP}"'
).read()

GATEWAY_URL = f"http://{INGRESS_HOST}:{INGRESS_PORT}/productpage"

# Define the lambda parameter for the Poisson distribution
# The lambda parameter is the average rate of value occurrence per interval
_lambda = 200 - 199

print("Starting script at", time.ctime())

for i in range(1, 501):
    requests.get(GATEWAY_URL)

    if i % 10 == 0:
        print("Sent", i, "requests so far...")

        # Compute the time to sleep using an exponential distribution
        # sleep_time = random.exponential(1 / _lambda)
        # time.sleep(sleep_time)

print("Script finished at", time.ctime())
