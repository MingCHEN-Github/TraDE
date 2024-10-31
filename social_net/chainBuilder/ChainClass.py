#Updated: 11 April, 2024
#define Chain Element (upStream_Microservice, downStrem_Microservice, stress)
from collections import defaultdict

class ChainElement:  # CE <UM, DM Stress>
    def __init__(self, upStream_MS, downStream_MS, stress):
        # define three attributes of for each ChainElement
        self.upStream_MS = upStream_MS
        self.downStream_MS = downStream_MS
        self.stress = stress
    
    def __repr__(self):
        return f"<{self.upStream_MS}, {self.downStream_MS}, {self.stress}>"

# define the ChainPath
class ChainPathAnalysis:
    def __init__(self, chain_elements):
        self.chain_elements = chain_elements
        self.chain_graph = defaultdict(list)
        self._build_stress_graph()

    def _build_stress_graph(self):
        for chain in self.chain_elements:
            self.chain_graph[chain.upStream_MS].append((chain.downStream_MS, chain.stress)) # building the path by appending dependent microservices(UM->DM)
    '''
    build example:
    # Create some chain elements
            chain_elements = [
                ChainElement('MS1', 'MS2', 10),
                ChainElement('MS1', 'MS3', 20),
                ChainElement('MS2', 'MS4', 30),
            ]
            # Create a ChainPathAnalysis instance
            analysis = ChainPathAnalysis(chain_elements)
            # analysis.chain_graph is a defaultdict and it looks like this, which shows one UM could have mutiple DM:
            # MS1->MS2 (with stress 10), MS1->MS3 (with stress 20), MS2->MS4 (with stress 30)
            # {'MS1': [('MS2', 10), ('MS3', 20)], 'MS2': [('MS4', 30)]}
    '''


    def _find_all_ChainPaths(self, start_MS, end_MS, path=[], stress_sum=0, count=0): # 'ms' is abbration for microservice
        path = path + [start_MS] # a single path
        if start_MS == end_MS:
            # return [(path, stress_sum/count if count > 0 else 0)]
            if count > 0:
                average_stress = stress_sum / count
            else:
                average_stress = 0
            return [(path, average_stress)]
        
        if start_MS not in self.chain_graph:
            return []
        paths = [] # store all found paths
        for new_MS, stress in self.chain_graph[start_MS]: 
            if new_MS not in path: # new_MS is not included in the path
                newpaths = self._find_all_ChainPaths(new_MS, end_MS, path, stress_sum + stress, count + 1)
                for newpath in newpaths:
                    paths.append(newpath) # add the found new paths
        return paths

    # find the longest path in current networking environment
    # sort chain paths based on each path's stress
    # def sort_chain_paths(self): 
    #     # Get all starting microservices
    #     start_MSs = set(self.chain_graph.keys())
    #     end_MSs = set([chain.downStream_MS for chain in self.chain_elements]) - start_MSs

    #     all_paths = []
    #     for start_MS in start_MSs:
    #         for end_MS in end_MSs:
    #             all_paths.extend(self._find_all_ChainPaths(start_MS, end_MS))

    #     # Sort all chain paths by path's average stress
    #     sorted_chain_paths = sorted(all_paths, key=lambda x: x[1], reverse=True)
    #     return sorted_chain_paths

    def sort_chain_paths(self):
        # Get all starting microservices
        start_microservices = set(self.chain_graph.keys())

        # Get all ending microservices by taking all downstream microservices
        # and removing any that are also starting microservices
        end_microservices = set()
        for chain in self.chain_elements:
            end_microservices.add(chain.downStream_MS)
        end_microservices = end_microservices - start_microservices

        # Find all paths from each starting microservice to each ending microservice
        all_paths = []
        for start in start_microservices:
            for end in end_microservices:
                paths = self._find_all_ChainPaths(start, end)
                all_paths.extend(paths)

        # Define a function to get the average stress of a path
        def get_average_stress(path):
            return path[1] # the value at path[1] is stress 

        # Sort all paths by their average stress in descending order
        sorted_paths = sorted(all_paths, key=get_average_stress, reverse=True)

        return sorted_paths
    
    
    def __repr__(self):
        return f"ChainPath Analysis with {len(self.chain_elements)} element chains"



# Old code in March 2024

# define critical chain elements and how to find, building, sorting the critical chains
# class ElementChain:
#     def __init__(self, upStream_pod, downStream_pod, frequency):
#         self.upStream_pod = upStream_pod
#         self.downStream_pod = downStream_pod
#         self.frequency = frequency
    
#     def __repr__(self):
#         return f"<{self.upStream_pod}, {self.downStream_pod}, {self.frequency}>"
# from collections import defaultdict

# class CriticalChainAnalysis:
#     def __init__(self, element_chains):
#         self.element_chains = element_chains
#         self.chain_graph = defaultdict(list)
#         self._build_graph()

#     def _build_graph(self):
#         for chain in self.element_chains:
#             self.chain_graph[chain.upStream_pod].append((chain.downStream_pod, chain.frequency))

#     def _find_all_paths(self, start_pod, end_pod, path=[], frequency_sum=0, count=0):
#         path = path + [start_pod]
#         if start_pod == end_pod:
#             return [(path, frequency_sum/count if count > 0 else 0)]
#         if start_pod not in self.chain_graph:
#             return []
#         paths = []
#         for node, freq in self.chain_graph[start_pod]:
#             if node not in path:
#                 newpaths = self._find_all_paths(node, end_pod, path, frequency_sum + freq, count + 1)
#                 for newpath in newpaths:
#                     paths.append(newpath)
#         return paths

#     def find_longest_critical_path(self):
#         # Assuming the start_pod and end_pod are known for simplification
#         # This can be adapted to dynamically find all start and end points
#         start_pods = set(self.chain_graph.keys())
#         end_pods = set([chain.downStream_pod for chain in self.element_chains]) - start_pods

#         all_paths = []
#         for start_pod in start_pods:
#             for end_pod in end_pods:
#                 all_paths.extend(self._find_all_paths(start_pod, end_pod))

#         # Sort by average frequency to find the critical path
#         critical_path = sorted(all_paths, key=lambda x: x[1], reverse=True)
#         return critical_path

#     def __repr__(self):
#         return f"Critical Chain Analysis with {len(self.element_chains)} element chains"
