import os
import platform
from typing import Dict

import click
import dpath.util
from docker import DockerClient

from swarm_cli.lib import load_required_yaml
from .environment import Environment
from ..logging import logger
from ...client import Client


class StackModeState:
    env: str

    cfg_data: dict
    cfg_basename: str
    cfg_environments: Dict[str, Dict]
    root_path: str

    current_env: Environment

    _client: DockerClient = None
    clients: Dict = dict()

    def _init_client(self):
        self._client = Client.from_env()
        self.clients[self._client.docker_host] = self._client

    def get_docker_client(self):
        if not self._client:
            self._init_client()
        return self._client

    def get_client_for_host_or_ip(self, host: str, ip: str):
        if host == platform.node():
            if platform.node() in self.clients:
                return self.clients[platform.node()]
            else:
                self.clients[platform.node()] = Client(base_url=None)
                return self.clients[platform.node()]
        node_conn_string = 'ssh://root@{}'.format(ip)
        if node_conn_string in self.clients:
            return self.clients[node_conn_string]
        else:
            self.clients[node_conn_string] = Client(base_url=node_conn_string)
            return self.clients[node_conn_string]

    def get_docker_client_for_node(self, node_id: str):
        node = self.get_docker_client().nodes.get(node_id)
        node_host = dpath.util.get(node.attrs, "Description/Hostname", default=None)
        node_ip = dpath.util.get(node.attrs, "Status/Addr", default=None)
        if node_ip == '0.0.0.0':
            node_ip = dpath.util.get(node.attrs, "ManagerStatus/Addr", default=None).split(":")[0]
        return self.get_client_for_host_or_ip(node_host, node_ip)

    def get_first_running_container_for_service(self, fqsn: str):
        service = self.get_docker_client().services.get(fqsn)
        tasks = service.tasks(filters={'name': fqsn, 'desired-state': 'running'})
        task = tasks[0] if len(tasks) > 0 else None
        if not task:
            logger.warn("No running task found for {}".format(fqsn))
            return None, None
        task_id = task['ID']
        node_id = task['NodeID']
        client = self.get_docker_client_for_node(node_id)
        # pprint.pprint(task, indent=4)
        container_id = dpath.util.get(task, "Status/ContainerStatus/ContainerID", default=None)
        state = dpath.util.get(task, "Status/State", default=None)
        if state != 'running':
            logger.warn("Task not running")
            return None, None
        return client.containers.get(container_id), client

    def initFromFile(self, path: str):
        self.cfg_data = load_required_yaml(path)
        self.root_path = os.path.dirname(path)
        self.cfg_basename = self.cfg_data['basename']
        self.cfg_environments = self.cfg_data['environments']

    def selectEnv(self, env: str):
        if env not in self.cfg_environments:
            click.secho('Cannot select environment {}, please check the config file'.format(env), fg='red', bold=True)
            exit(1)
        self.env = env
        self.current_env = Environment(self.env, self.cfg_basename, self.cfg_environments[env])

        if self.current_env.cfg.production:
            click.confirm('You are going to run on a PRODUCTION swarm. Confirm?', abort=True)

        self.current_env.base_path = os.path.join(self.root_path, self.env)
        self.current_env.stack_base_name = self.cfg_basename
        self.current_env.add_stack_file(os.path.join(self.root_path, self.env, 'docker-compose.yml'))
        if self.current_env.cfg.docker_host is not None:
            os.environ['DOCKER_HOST'] = self.current_env.cfg.docker_host
        os.environ['STACK_NAME'] = self.current_env.cfg.stack_name
