import socket

from docker import DockerClient

from swarm_cli.lib.logging import logger


class Client(DockerClient):
    docker_host: str

    def __init__(self, *args, base_url: str = None, **kwargs):
        logger.notice('Connecting to docker at {}'.format(base_url))
        if base_url is not None and 'ssh://' in base_url:
            host = base_url.strip("ssh://").split('@')[1]
            ip = socket.gethostbyname(host)
            base_url = base_url.replace(host, ip)
            logger.verbose('Retrieved ip, new base_url {}'.format(base_url))
        self.docker_host = base_url
        super().__init__(*args, base_url=base_url, **kwargs)
