FROM python:3.10
RUN pip install kubernetes requests

# Copy the kubeconfig file
COPY config /root/.kube/config

COPY scheduler_logic.py /scheduler_logic.py
CMD python /scheduler_logic.py