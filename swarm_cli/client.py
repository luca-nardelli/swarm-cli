from docker import DockerClient

from swarm_cli.lib.logging import logger


class Client(DockerClient):
    docker_host: str

    def __init__(self, *args, base_url=None, **kwargs):
        self.docker_host = base_url
        logger.notice('Connecting to docker at {}'.format(base_url))
        super().__init__(*args, base_url=base_url, **kwargs)
