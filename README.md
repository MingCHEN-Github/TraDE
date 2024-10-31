# TraDE: Network and Traffic-aware AdaptiveScheduling for Microservices Under Dynamics


The transition from monolithic architecture to microservices has enhanced flexibility in application design and its scalable execution.
This approach often involves using a computing cluster managed by
a container orchestration platform, which supports the deployment of
microservices. However, this shift introduces significant challenges, particularly
in the efficient scheduling of containerized services. These challenges
are compounded by unpredictable scenarios such as dynamic
incoming workloads with various execution traffic and variable communication
delays among cluster nodes. Existing works often overlook the
real-time traffic impacts of dynamic requests on running microservices,
as well as the varied communication delays across cluster nodes.
Consequently, even optimally deployed microservices could suffer from
significant performance degradation over time. To address these issues,
we introduce a network and traffic-aware adaptive scheduling framework,
TraDE. This framework can adaptively redeploy microservice
containers to maintain desired performance amid changing traffic and
network conditions within the hosting cluster. We have implemented
TraDE as an extension to the Kubernetes platform. Additionally, we
deployed realistic microservice applications in a real compute cluster
and conducted extensive experiments to assess our framework’s performance
in various scenarios. The results demonstrate the effectiveness
of TraDE in rescheduling running microservices to enhance end-to-end
performance while maintaining a high goodput ratio. Compared with
the existing method NetMARKS, TraDE outperforms these methods by
reducing the average response time of the application by up to 48.3%,
and improving the throughput by up to 1.4x while maintaining a goodput
ratio of 95.36% and showing robust adaptive capability under sustained
workloads.
