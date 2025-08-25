from typing import Dict, Optional, Tuple
from console_link.models.client_options import ClientOptions
from console_link.models.kubectl_runner import KubectlRunner
from console_link.models.replayer_base import Replayer, ReplayStatus
from console_link.domain.exceptions.replay_errors import ReplayError

import logging

logger = logging.getLogger(__name__)


class K8sReplayer(Replayer):
    def __init__(self, config: Dict, client_options: Optional[ClientOptions] = None) -> None:
        super().__init__(config)
        self.client_options = client_options
        self.k8s_config = self.config["k8s"]
        self.namespace = self.k8s_config["namespace"]
        self.deployment_name = self.k8s_config["deployment_name"]
        self.kubectl_runner = KubectlRunner(namespace=self.namespace, deployment_name=self.deployment_name)

    def start(self, *args, **kwargs) -> str:
        logger.info(f"Starting K8s replayer by setting desired count to {self.default_scale} instances")
        return self.kubectl_runner.perform_scale_command(replicas=self.default_scale)

    def stop(self, *args, **kwargs) -> str:
        logger.info("Stopping K8s replayer by setting desired count to 0 instances")
        return self.kubectl_runner.perform_scale_command(replicas=0)

    def get_status(self, *args, **kwargs) -> Tuple[ReplayStatus, str]:
        deployment_status = self.kubectl_runner.retrieve_deployment_status()
        logger.info(f"Get status K8s replayer: {deployment_status}")
        if not deployment_status:
            raise ReplayError("Failed to get deployment status for Replayer")
        status_str = str(deployment_status)
        if deployment_status.terminating > 0 and deployment_status.desired == 0:
            return (ReplayStatus.TERMINATING, status_str)
        if deployment_status.running > 0:
            return (ReplayStatus.RUNNING, status_str)
        if deployment_status.desired > 0:
            return (ReplayStatus.STARTING, status_str)
        return (ReplayStatus.STOPPED, status_str)

    def scale(self, units: int, *args, **kwargs) -> str:
        logger.info(f"Scaling K8s replayer by setting desired count to {units} instances")
        return self.kubectl_runner.perform_scale_command(replicas=units)
