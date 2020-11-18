import json
import time
from datetime import datetime, timedelta


class KubernetesTools:
    @staticmethod
    def get_tiller_rbac_setup() -> str:
        return '''apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  annotations:
    rbac.authorization.kubernetes.io/autoupdate: "true"
  labels:
    kubernetes.io/bootstrapping: rbac-defaults
  name: cluster-admin
rules:
- apiGroups:
  - '*'
  resources:
  - '*'
  verbs:
  - '*'
- nonResourceURLs:
  - '*'
  verbs:
  - '*'
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: tiller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: tiller
    namespace: kube-system
'''

    @staticmethod
    def apply(dockerNetwork: str, kubeConfig: str, applyYaml: str, shell_executor: object) -> bool:
        cmd = [
            'docker',
            'run',
            '-i',
            '--rm',
            '--network',
            dockerNetwork,
            '--volume',
            f'{kubeConfig}:/tmp/kube_config',
            'bitnami/kubectl:1.18',
            '--kubeconfig',
            '/tmp/kube_config',
            'apply',
            '-f',
            '-']
        return shell_executor.execute(cmd, piped_input=applyYaml) == 0

    @staticmethod
    def wait_for_deployment(dockerNetwork: str, kubeConfig: str, namespace: str, deploymentName: str, timeout: float, shell_executor: object, sleeper: object) -> bool:
        '''
        Waits for a Kubernetes deployment to become available (availableReplicas > 0)
        '''
        startTime = datetime.now()
        while True:
            cmd = [
                'docker',
                'run',
                '-i',
                '--rm',
                '--network',
                dockerNetwork,
                '--volume',
                f'{kubeConfig}:/tmp/kube_config',
                'bitnami/kubectl:1.18',
                '--kubeconfig',
                '/tmp/kube_config',
                '--namespace',
                namespace,
                'get',
                'deployments',
                deploymentName,
                '-o',
                'json'
            ]
            deploymentJson = shell_executor.get_output(cmd)
            deployment = json.loads(deploymentJson)
            if 'status' in deployment and 'availableReplicas' in deployment['status'] and deployment['status']['availableReplicas'] > 0:
                return True
            else:
                currentTime = datetime.now()
                timeElapsed = currentTime - startTime
                if timeElapsed.total_seconds() > timeout:
                    print(deploymentJson)
                    return False
                else:
                  sleeper.sleep(1)

    @staticmethod
    def kubectl(dockerNetwork: str, kubeConfig: str, variables: set, commands: list, shell_executor: object) -> int:
      cmd = [
        "/bin/sh",
        "-c",
        " ".join([
          'docker',
          'run',
          '-i',
          '--rm',
          '--network',
          dockerNetwork,
          '--volume',
          f'{kubeConfig}:/tmp/kube_config'] + \
          [arg for args in [["--env", variable] for variable in variables] for arg in args] + \
          ['bitnami/kubectl:1.18',
          '--kubeconfig',
          '/tmp/kube_config'] + commands)
      ]
      return shell_executor.execute(cmd)
