'''microservice-node mapping placement'''
# import seaborn as sns
# import pandas as pd
# import matplotlib.pyplot as plt
# import numpy as np
# import random
import multiprocessing as mp
# from timeit import default_timer as timer
# Define the functions for placement and cost calculation
def calculate_communication_cost(exec_graph, placement, delay_matrix):
    cost = 0
    for u in range(len(exec_graph)):
        for v in range(len(exec_graph[u])):
            if exec_graph[u][v] > 0:
                server_u = placement[u]
                server_v = placement[v]
                cost += exec_graph[u][v] * delay_matrix[server_u][server_v]
    return cost

def greedy_placement_worker(exec_graph, delay_matrix, placement, num_servers, start, end):
    current_cost = calculate_communication_cost(exec_graph, placement, delay_matrix)
    improved = True
    while improved:
        improved = False
        for u in range(start, end):
            current_server = placement[u]
            for new_server in range(num_servers):
                if new_server != current_server:
                    new_placement = placement.copy()
                    new_placement[u] = new_server
                    new_cost = calculate_communication_cost(exec_graph, new_placement, delay_matrix)
                    if new_cost < current_cost:
                        placement = new_placement
                        current_cost = new_cost
                        improved = True
                        break
            if improved:
                break
    return placement, current_cost

# divides the placement optimization task into chunks and runs them in parallel using multiple worker processes.
def parallel_greedy_placement(exec_graph, delay_matrix, placement, num_servers, num_workers=4):
    num_microservices = len(exec_graph)
    chunk_size = (num_microservices + num_workers - 1) // num_workers  # Adjust chunk size to cover all microservices
    print(f"{chunk_size} = ({num_microservices} + {num_workers} - 1) // {num_workers}")

    while True:
        pool = mp.Pool(num_workers)
        chunks = [(exec_graph, delay_matrix, placement, num_servers, i*chunk_size, min((i+1)*chunk_size, num_microservices)) for i in range(num_workers)] #divides the placement optimization task into chunks
        results = pool.starmap(greedy_placement_worker, chunks) #distributes the chunks to the worker processes and collects their results
        pool.close() #prevents any more tasks from being submitted to the pool
        pool.join() #waits for all worker processes to finish

        # print("Chunks:", chunks)
        print("lengnths of results:", len(results))
        print("Results:", results)
        # Find the best result from all chunks
        new_placement = results[0][0] #initializes the best placement and cost with the first result
        new_cost = results[0][1] #initializes the best placement and cost with the first result
        improved = False

        for result in results[1:]:
            if result[1] < new_cost:
                new_placement = result[0]
                new_cost = result[1]
                improved = True

        if not improved:
            break

        placement = new_placement

    return placement, new_cost