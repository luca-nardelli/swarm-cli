import os
from typing import Dict

import click
import docker
from docker import DockerClient

from swarm_cli.lib import load_required_yaml
from .environment import Environment


class StackModeState:
    env: str

    cfg_data: dict
    cfg_basename: str
    cfg_environments: Dict[str, Dict]
    root_path: str

    current_env: Environment

    client: DockerClient = None

    def _init_client(self):
        self.client = docker.from_env()

    def get_docker_client(self):
        if not self.client:
            self._init_client()
        return self.client

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
        self._init_client()
