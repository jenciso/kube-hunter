import logging
import json
import requests
import uuid

from ...core.events import handler
from ...core.events.types import Vulnerability, Event
from ..discovery.apiserver import ApiServer
from ...core.types import Hunter, ActiveHunter, KubernetesCluster, RemoteCodeExec, AccessRisk, InformationDisclosure


""" Vulnerabilities """


class ServerApiAccess(Vulnerability, Event):
    """ Accessing the server API within a compromised pod would help an attacker gain full control over the cluster"""

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Access to server API", category=RemoteCodeExec)
        self.evidence = evidence


class ListPodUnderDefaultNamespace(Vulnerability, Event):
    """ Accessing the pods list under default namespace might give an attacker valuable
     information to harm the cluster """

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Listing pods list under default namespace",
                               category=InformationDisclosure)
        self.evidence = evidence


class ListPodUnderAllNamespaces(Vulnerability, Event):
    """ Accessing the pods list under ALL of the namespaces might give an attacker valuable information"""

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Listing pods list under ALL namespaces",
                               category=InformationDisclosure)
        self.evidence = evidence


class ListAllNamespaces(Vulnerability, Event):
    """ Accessing all of the namespaces might give an attacker valuable information """

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Listing all namespaces",
                               category=InformationDisclosure)
        self.evidence = evidence


class ListAllRoles(Vulnerability, Event):
    """ Accessing all of the roles might give an attacker valuable information """

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Listing all roles",
                               category=InformationDisclosure)
        self.evidence = evidence


class ListAllRolesUnderDefaultNamespace(Vulnerability, Event):
    """ Accessing all of the roles under default namespace might give an attacker valuable information """

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Listing all roles under default namespace",
                               category=InformationDisclosure)
        self.evidence = evidence


class ListAllClusterRoles(Vulnerability, Event):
    """ Accessing all of the cluster roles might give an attacker valuable information """

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Listing all cluster roles",
                               category=InformationDisclosure)
        self.evidence = evidence


class CreateANamespace(Vulnerability, Event):

    """ Creating a namespace might give an attacker an area with default (exploitable) permissions to run pods in.
    """
    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Created a namespace",
                               category=AccessRisk)
        self.evidence = evidence


class DeleteANamespace(Vulnerability, Event):

    """ Deleting a namespace might give an attacker the option to affect application behavior """
    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Delete a namespace",
                               category=AccessRisk)
        self.evidence = evidence


class CreateARole(Vulnerability, Event):
    """ Creating a role might give an attacker the option to harm the normal behavior of newly created pods
     within the specified namespaces.
    """

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Created a role",
                               category=AccessRisk)
        self.evidence = evidence


class CreateAClusterRole(Vulnerability, Event):
    """ Creating a cluster role might give an attacker the option to harm the normal behavior of newly created pods
     across the whole cluster
    """

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Created a cluster role",
                               category=AccessRisk)
        self.evidence = evidence


class PatchARole(Vulnerability, Event):
    """ Patching a role might give an attacker the option to create new pods with custom roles within the
    specific role's namespace scope
    """

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Patched a role",
                               category=AccessRisk)
        self.evidence = evidence


class PatchAClusterRole(Vulnerability, Event):
    """ Patching a cluster role might give an attacker the option to create new pods with custom roles within the whole
    cluster scope.
    """

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Patched a cluster role",
                               category=AccessRisk)
        self.evidence = evidence


class DeleteARole(Vulnerability, Event):
    """ Deleting a role might allow an attacker to affect access to resources in the namespace"""

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Deleted a role",
                               category=AccessRisk)
        self.evidence = evidence


class DeleteAClusterRole(Vulnerability, Event):
    """ Deleting a cluster role might allow an attacker to affect access to resources in the cluster"""

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Deleted a cluster role",
                               category=AccessRisk)
        self.evidence = evidence


class CreateAPod(Vulnerability, Event):
    """ Creating a new pod allows an attacker to run custom code"""

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Created A Pod",
                               category=AccessRisk)
        self.evidence = evidence


class CreateAPrivilegedPod(Vulnerability, Event):
    """ Creating a new PRIVILEGED pod would gain an attacker FULL CONTROL over the cluster"""

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Created A PRIVILEGED Pod",
                               category=AccessRisk)
        self.evidence = evidence


class PatchAPod(Vulnerability, Event):
    """ Patching a pod allows an attacker to compromise and control it """

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Patched A Pod",
                               category=AccessRisk)
        self.evidence = evidence


class DeleteAPod(Vulnerability, Event):
    """ Deleting a pod allows an attacker to disturb applications on the cluster """

    def __init__(self, evidence):
        Vulnerability.__init__(self, KubernetesCluster, name="Deleted A Pod",
                               category=AccessRisk)
        self.evidence = evidence


class ApiServerPassiveHunterFinished(Event):
    def __init__(self, all_namespaces_names, service_account_token, host, port):
        self.host = host
        self.port = port
        self.all_namespaces_names = all_namespaces_names
        self.service_account_token = service_account_token

    def __str__(self):
        return str(self.service_account_token)


# Passive Hunter
@handler.subscribe(ApiServer)
class AccessApiServerViaServiceAccountToken(Hunter):
    """ API Server Hunter
    Accessing the API server within a compromised pod might grant an attacker full control over the cluster
    """

    def __init__(self, event):
        self.event = event
        self.headers = dict()
        self.path = "https://{}:{}".format(self.event.host, self.event.port)

        self.api_server_evidence = ''
        self.service_account_token_evidence = ''
        self.pod_list_under_default_namespace_evidence = ''
        self.pod_list_under_all_namespaces_evidence = ''

        self.all_namespaces_names_evidence = list()
        self.all_roles_names_evidence = list()
        self.roles_names_under_default_namespace_evidence = list()
        self.all_cluster_roles_names_evidence = list()
        self.namespaces_and_their_pod_names = list(dict())

    def access_api_server(self):
        logging.debug(self.event.host)
        logging.debug('Passive Hunter is attempting to access the API server using the pod\'s service account token')
        try:
            res = requests.get("{path}/api".format(path=self.path),
                               headers=self.headers, verify=False)
            self.api_server_evidence = res.content
            return res.status_code == 200 and res.content != ''
        except requests.exceptions.ConnectionError:
            return False

    def get_service_account_token(self):
        logging.debug(self.event.host)
        logging.debug('Passive Hunter is attempting to access pod\'s service account token')
        try:
            with open('/var/run/secrets/kubernetes.io/serviceaccount/token', 'r') as token:
                data = token.read()
                self.service_account_token_evidence = data
                self.headers = {'Authorization': 'Bearer ' + self.service_account_token_evidence}
                return True
        except IOError:  # Couldn't read file
            return False

    # 1 Pods Method:
    def get_pods_list_under_requested_scope(self, scope=None):
        try:
            res = requests.get("{path}/api/v1/{scope}/pods".format(path=self.path, scope=scope),
                               headers=self.headers, verify=False)

            parsed_response_content = json.loads(res.content)
            for item in parsed_response_content["items"]:
                name = item["metadata"]["name"].encode('ascii', 'ignore')
                namespace = item["metadata"]["namespace"].encode('ascii', 'ignore')
                self.namespaces_and_their_pod_names.append({'name': name, 'namespace': namespace})

            return res.status_code == 200
        except (requests.exceptions.ConnectionError, KeyError):
            return False

    # 1 Namespace method:
    def get_all_namespaces(self):
        try:
            res = requests.get("{path}/api/v1/namespaces".format(path=self.path),
                                                                 headers=self.headers,
                                                                 verify=False)

            parsed_response_content = json.loads(res.content)
            for item in parsed_response_content["items"]:
                self.all_namespaces_names_evidence.append(item["metadata"]["name"].encode('ascii', 'ignore'))
            return res.status_code == 200
        except (requests.exceptions.ConnectionError, KeyError):
            return False

    # 3 Roles & Cluster Roles Methods:
    def get_roles_under_default_namespace(self):
        try:
            res = requests.get("{path}/apis/rbac.authorization.k8s.io/v1/namespaces/default/roles".format(
                                 path=self.path),
                               headers=self.headers, verify=False)
            parsed_response_content = json.loads(res.content)
            for item in parsed_response_content["items"]:
                self.roles_names_under_default_namespace_evidence.append(item["metadata"]["name"].encode('ascii', 'ignore'))
            return res.content if res.status_code == 200 else False
        except (requests.exceptions.ConnectionError, KeyError):
            return False

    def get_all_cluster_roles(self):
        try:
            res = requests.get("{path}/apis/rbac.authorization.k8s.io/v1/clusterroles".format(
                                 path=self.path),
                               headers=self.headers, verify=False)
            parsed_response_content = json.loads(res.content)
            for item in parsed_response_content["items"]:
                self.all_cluster_roles_names_evidence.append(item["metadata"]["name"].encode('ascii', 'ignore'))
            return res.content if res.status_code == 200 else False
        except (requests.exceptions.ConnectionError, KeyError):
            return False

    def get_all_roles(self):
        try:
            res = requests.get("{path}/apis/rbac.authorization.k8s.io/v1/roles".format(
                                 path=self.path),
                               headers=self.headers, verify=False)
            parsed_response_content = json.loads(res.content)
            for item in parsed_response_content["items"]:
                self.all_roles_names_evidence.append(item["metadata"]["name"].encode('ascii', 'ignore'))
            return res.content if res.status_code == 200 else False
        except (requests.exceptions.ConnectionError, KeyError):
            return False

    def execute(self):

        self.get_service_account_token()

        if self.access_api_server():
            self.publish_event(ServerApiAccess(self.api_server_evidence))

        if self.get_all_namespaces():
            self.publish_event(ListAllNamespaces(self.all_namespaces_names_evidence))

        if self.get_pods_list_under_requested_scope():
            self.publish_event(ListPodUnderAllNamespaces(self.namespaces_and_their_pod_names))
        else:
            if self.get_pods_list_under_requested_scope(scope='namespaces/default'):
                self.publish_event(ListPodUnderDefaultNamespace(self.namespaces_and_their_pod_names))

        if self.get_all_roles():
            self.publish_event(ListAllRoles(self.all_roles_names_evidence))
        else:
            if self.get_roles_under_default_namespace():
                self.publish_event(ListAllRolesUnderDefaultNamespace(
                                        self.roles_names_under_default_namespace_evidence))
        if self.get_all_cluster_roles():
            self.publish_event(ListAllClusterRoles(self.all_cluster_roles_names_evidence))

        # At this point we know we got the service_account_token, and we might got all of the namespaces
        self.publish_event(ApiServerPassiveHunterFinished(self.all_namespaces_names_evidence,
                                                          self.service_account_token_evidence,
                                                          self.event.host, self.event.port))


# Active Hunter
@handler.subscribe(ApiServerPassiveHunterFinished)
class AccessApiServerViaServiceAccountTokenActive(ActiveHunter):
    """API server hunter
    Accessing the api server might grant an attacker full control over the cluster
    """

    def __init__(self, event):
        self.event = event
        self.path = "https://{}:{}".format(self.event.host, self.event.port)

        # Getting Passive hunter's data:
        self.namespaces_and_their_pod_names = dict()
        self.all_namespaces_names = set(event.all_namespaces_names)
        self.service_account_token = event.service_account_token

        # 12 Evidences:
        self.is_privileged_pod_created = False
        self.created_pod_name_evidence = ''
        self.patched_newly_created_pod_evidence = ''
        self.deleted_newly_created_pod_evidence = ''

        self.created_role_evidence = ''
        self.patched_newly_created_role_evidence = ''
        self.deleted_newly_created_role_evidence = ''

        self.created_cluster_role_evidence = ''
        self.patched_newly_created_cluster_role_evidence = ''
        self.deleted_newly_created_cluster_role_evidence = ''

        self.created_new_namespace_name_evidence = ''
        self.deleted_new_namespace_name_evidence = ''

    # 3 Pod methods:
    def create_a_pod(self, namespace, is_privileged):
        if is_privileged and self.is_privileged_pod_created:  # We don't want to create more than 1 privileged pod.
            return False
        privileged_value = ',"securityContext":{"privileged":true}' if is_privileged else ''
        json_pod = \
            """

                {{"apiVersion": "v1",
                "kind": "Pod",
                "metadata": {{
                    "name": "{random_str}"
                }},
                "spec": {{
                    "containers": [
                        {{
                            "name": "{random_str}",
                            "image": "nginx:1.7.9",
                            "ports": [
                                {{
                                    "containerPort": 80
                                }}
                            ]
                            {is_privileged_flag}
                        }}
                    ]
                }}
            }}

            """.format(random_str=(str(uuid.uuid4()))[0:5], is_privileged_flag=privileged_value)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {token}'.format(token=self.service_account_token)
        }
        try:
            res = requests.post("{path}/api/v1/namespaces/{namespace}/pods".format(
                                path=self.path, namespace=namespace),
                                verify=False, data=json_pod, headers=headers)
            if res.status_code not in [200, 201, 202]: return False

            parsed_content = json.loads(res.content)
            self.created_pod_name_evidence = parsed_content['metadata']['name']
        except (requests.exceptions.ConnectionError, KeyError):
            return False
        if is_privileged:
            self.is_privileged_pod_created = True
        return True

    def delete_a_pod(self, namespace, pod_name):
        try:
            res = requests.delete("{path}/api/v1/namespaces/{namespace}/pods/{name}".format(
                                 path=self.path, name=pod_name, namespace=namespace),
                               headers={'Authorization': 'Bearer ' + self.service_account_token}, verify=False)
            if res.status_code not in [200, 201, 202]: return False
            parsed_content = json.loads(res.content)
            self.deleted_newly_created_pod_evidence = parsed_content['metadata']['deletionTimestamp']
        except (requests.exceptions.ConnectionError, KeyError):
            return False
        return True

    def patch_a_pod(self, namespace, pod_name):
        #  Initialize request variables:
        patch_data = '[{ "op": "add", "path": "/hello", "value": ["world"] }]'
        headers = {
            'Content-Type': 'application/json-patch+json',
            'Authorization': 'Bearer {token}'.format(token=self.service_account_token)
        }
        try:
            res = requests.patch("{path}/api/v1/namespaces/{namespace}/pods/{name}".format(
                                 path=self.path, namespace=namespace, name=pod_name),
                                 headers=headers, verify=False, data=patch_data)
            if res.status_code not in [200, 201, 202]: return False
            parsed_content = json.loads(res.content)
            self.patched_newly_created_pod_evidence = parsed_content['metadata']['namespace']
        except (requests.exceptions.ConnectionError, KeyError):
            return False
        return True

    # 2 Namespaces methods:
    def create_namespace(self):
        #  Initialize request variables:
        json_namespace = '{{"kind":"Namespace","apiVersion":"v1","metadata":{{"name":"{random_str}","labels":{{"name":"{random_str}"}}}}}}'.format(random_str=(str(uuid.uuid4()))[0:5])
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {token}'.format(token=self.service_account_token)
        }
        try:
            res = requests.post("{path}/api/v1/namespaces".format(
                path=self.path),
                verify=False, data=json_namespace, headers=headers)
            if res.status_code not in [200, 201, 202]: return False
            parsed_content = json.loads(res.content)
            self.created_new_namespace_name_evidence = parsed_content['metadata']['name']
            self.all_namespaces_names.add(self.created_new_namespace_name_evidence)
        except (requests.exceptions.ConnectionError, KeyError):  # e.g. DNS failure, refused connection, etc
            return False
        return True

    # 2 Namespaces methods:
    def delete_namespace(self):
        #  Initialize request header:
        headers = {
            'Authorization': 'Bearer {token}'.format(token=self.service_account_token)
        }
        try:
            res = requests.delete("{path}/api/v1/namespaces/{name}".format(
                path=self.path, name=self.created_new_namespace_name_evidence),
                verify=False,  headers=headers)
            if res.status_code != 200: return False
            parsed_content = json.loads(res.content)
            self.deleted_new_namespace_name_evidence = parsed_content['metadata']['name']
            self.all_namespaces_names.remove(self.created_new_namespace_name_evidence)
        except (requests.exceptions.ConnectionError, KeyError):  # e.g. DNS failure, refused connection, etc
            return False
        return True

    #  6 Roles & Cluster roles Methods:
    def create_a_role(self, namespace):
        #  Initialize request variables:
        role_json = """{{
                          "kind": "Role",
                          "apiVersion": "rbac.authorization.k8s.io/v1",
                          "metadata": {{
                            "namespace": "{namespace}",
                            "name": "{random_str}"
                          }},
                          "rules": [
                            {{
                              "apiGroups": [
                                ""
                              ],
                              "resources": [
                                "pods"
                              ],
                              "verbs": [
                                "get",
                                "watch",
                                "list"
                              ]
                            }}
                          ]
                        }}""".format(random_str=(str(uuid.uuid4()))[0:5], namespace=namespace)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {token}'.format(token=self.service_account_token)
        }
        try:
            res = requests.post("{path}/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/roles".format(
                                path=self.path, namespace=namespace),
                                headers=headers, verify=False, data=role_json)
            if res.status_code not in [200, 201, 202]: return False
            parsed_content = json.loads(res.content)
            self.created_role_evidence = parsed_content['metadata']['name']
        except (requests.exceptions.ConnectionError, KeyError):
            return False
        return True

    def create_a_cluster_role(self):
        #  Initialize request variables:
        cluster_role_json = """{{
                      "kind": "ClusterRole",
                      "apiVersion": "rbac.authorization.k8s.io/v1",
                      "metadata": {{
                        "name": "{random_str}"
                      }},
                      "rules": [
                        {{
                          "apiGroups": [
                            ""
                          ],
                          "resources": [
                            "pods"
                          ],
                          "verbs": [
                            "get",
                            "watch",
                            "list"
                          ]
                        }}
                      ]
                    }}""".format(random_str=(str(uuid.uuid4()))[0:5])
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {token}'.format(token=self.service_account_token)
        }
        try:
            res = requests.post("{path}/apis/rbac.authorization.k8s.io/v1/clusterroles".format(
                               path=self.path),
                               headers=headers, verify=False, data=cluster_role_json)
            if res.status_code not in [200, 201, 202]: return False
            parsed_content = json.loads(res.content)
            self.created_cluster_role_evidence = parsed_content['metadata']['name']
        except (requests.exceptions.ConnectionError, KeyError):
            return False
        return True

    def delete_a_role(self, namespace, newly_created_role_name):
        try:
            res = requests.delete("{path}/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/roles/{role}".format(
                                 path=self.path, namespace=namespace, role=newly_created_role_name),
                               headers={'Authorization': 'Bearer ' + self.service_account_token}, verify=False)
            if res.status_code not in [200, 201, 202]: return False
            parsed_content = json.loads(res.content)
            self.deleted_newly_created_role_evidence = parsed_content["status"]
        except (requests.exceptions.ConnectionError, KeyError):
            return False
        return True

    def delete_a_cluster_role(self, newly_created_cluster_role_name):
        try:
            res = requests.delete("{path}/apis/rbac.authorization.k8s.io/v1/clusterroles/{name}".format(
                                 path=self.path, name=newly_created_cluster_role_name),
                               headers={'Authorization': 'Bearer ' + self.service_account_token}, verify=False)
            if res.status_code not in [200, 201, 202]: return False
            parsed_content = json.loads(res.content)
            self.deleted_newly_created_cluster_role_evidence = parsed_content["status"]
        except (requests.exceptions.ConnectionError, KeyError):
            return False
        return True

    def patch_a_role(self, namespace, newly_created_role_name):
        #  Initialize request variables:
        patch_data = '[{ "op": "add", "path": "/hello", "value": ["world"] }]'
        headers = {
            'Content-Type': 'application/json-patch+json',
            'Authorization': 'Bearer {token}'.format(token=self.service_account_token)
        }
        try:
            res = requests.patch("{path}/apis/rbac.authorization.k8s.io/v1/namespaces/{namespace}/roles/{name}".format(
                                 path=self.path, name=newly_created_role_name,
                                 namespace=namespace),
                                 headers=headers,
                                 verify=False, data=patch_data)
            if res.status_code not in [200, 201, 202]: return False
            parsed_content = json.loads(res.content)
            self.patched_newly_created_role_evidence = parsed_content['metadata']['name']
        except (requests.exceptions.ConnectionError, KeyError):
            return False
        return True

    def patch_a_cluster_role(self, newly_created_cluster_role_name):

        patch_data = '[{ "op": "add", "path": "/hello", "value": ["world"] }]'
        headers = {
            'Content-Type': 'application/json-patch+json',
            'Authorization': 'Bearer {token}'.format(token=self.service_account_token)
        }
        try:
            res = requests.patch("{path}/apis/rbac.authorization.k8s.io/v1/clusterroles/{name}".format(
                                 path=self.path, name=newly_created_cluster_role_name),
                                 headers=headers,
                                 verify=False, data=patch_data)
            if res.status_code not in [200, 201, 202]: return False
            parsed_content = json.loads(res.content)
            self.patched_newly_created_cluster_role_evidence = parsed_content['metadata']['name']
        except (requests.exceptions.ConnectionError, KeyError):
            return False
        return True

    def execute(self):
        if self.service_account_token != '':
            #  Namespaces Api Calls:
            if self.create_namespace():
                self.publish_event(CreateANamespace('new namespace name: {name}'.
                                                         format(name=self.created_new_namespace_name_evidence)))
                if self.delete_namespace():
                    self.publish_event(DeleteANamespace(self.deleted_new_namespace_name_evidence))

            #  Cluster Roles Api Calls:
            if self.create_a_cluster_role():
                self.publish_event(CreateAClusterRole('Cluster role name:  {name}'.format(
                                                      name=self.created_cluster_role_evidence)))
                if self.patch_a_cluster_role(self.created_cluster_role_evidence):

                    self.publish_event(PatchAClusterRole('Patched Cluster Role Name:  {name}'.format(
                                                          name=self.patched_newly_created_cluster_role_evidence)))

                if self.delete_a_cluster_role(self.created_cluster_role_evidence):
                    self.publish_event(DeleteAClusterRole('Cluster role status:  {status}'.format(
                                                           status=self.deleted_newly_created_cluster_role_evidence)))

            #  Operating on pods over all namespaces:
            for namespace in self.all_namespaces_names:
                # Pods Api Calls:
                if self.create_a_pod(namespace, True) or self.create_a_pod(namespace, False):

                    if self.is_privileged_pod_created:
                        self.publish_event(CreateAPrivilegedPod('Pod Name: {pod_name}  Pod Namespace: {pod_namespace}'.format(
                                                  pod_name=self.created_pod_name_evidence, pod_namespace=namespace)))
                    else:
                        self.publish_event(CreateAPod('Pod Name: {pod_name}  Pod Namespace: {pod_namespace}'.format(
                                                      pod_name=self.created_pod_name_evidence, pod_namespace=namespace)))

                    if self.patch_a_pod(namespace, self.created_pod_name_evidence):
                        self.publish_event(PatchAPod('Pod Name: {pod_name}  Pod namespace: {patch_evidence}'.format(
                                                     pod_name=self.created_pod_name_evidence,
                                                     patch_evidence=self.patched_newly_created_pod_evidence)))

                    if self.delete_a_pod(namespace, self.created_pod_name_evidence):
                        self.publish_event(DeleteAPod('Pod Name: {pod_name}  deletion time: {delete_evidence}'.format(
                                                     pod_name=self.created_pod_name_evidence,
                                                     delete_evidence=self.deleted_newly_created_pod_evidence)))
                # Roles Api Calls:
                if self.create_a_role(namespace):
                    self.publish_event(CreateARole('Role name:  {name}'.format(
                        name=self.created_role_evidence)))

                    if self.patch_a_role(namespace, self.created_role_evidence):
                        self.publish_event(PatchARole('Patched Role Name:  {name}'.format(
                            name=self.patched_newly_created_role_evidence)))

                    if self.delete_a_role(namespace, self.created_role_evidence):
                        self.publish_event(DeleteARole('Role Status response: {status}'.format(
                            status=self.deleted_newly_created_role_evidence)))


            #  Note: we are not binding any role or cluster role because
            # -- in certain cases it might effect the running pod within the cluster (and we don't want to do that).
