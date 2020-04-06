import docker
from docker.models.containers import Container

from swarm_cli.lib.logging import logger


def get_first_running_container_for_service(client: docker.DockerClient, fqsn: str):
    elements = client.containers.list(filters={'name': fqsn, 'status': 'running'})
    docker_container: Container = elements[0] if len(elements) > 0 else None
    if not docker_container:
        logger.warn("No running container found for {}".format(fqsn))
    return docker_container
