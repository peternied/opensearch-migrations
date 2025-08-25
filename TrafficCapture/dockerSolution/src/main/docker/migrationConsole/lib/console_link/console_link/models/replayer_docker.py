from typing import Dict, Tuple
from console_link.models.replayer_base import Replayer, ReplayStatus

import logging

logger = logging.getLogger(__name__)


class DockerReplayer(Replayer):
    def __init__(self, config: Dict) -> None:
        super().__init__(config)

    def start(self, *args, **kwargs) -> str:
        logger.warning("Start command is not implemented for Docker Replayer")
        return "No action performed, action is unimplemented"

    def stop(self, *args, **kwargs) -> str:
        logger.warning("Stop command is not implemented for Docker Replayer")
        return "No action performed, action is unimplemented"

    def get_status(self, *args, **kwargs) -> Tuple[ReplayStatus, str]:
        logger.warning("Get status command is not implemented for Docker Replayer and "
                       "always assumes service is running")
        return (ReplayStatus.RUNNING, "Docker Replayer is assumed to be running")

    def scale(self, units: int, *args, **kwargs) -> str:
        raise NotImplementedError()
