import os.path
from typing import Dict, List

from swarm_cli.lib import load_required_yaml
from swarm_cli.lib.logging import logger
from swarm_cli.lib.utils import parse_yaml_bool


class Environment:
    class Config:
        stack_name: str
        docker_host: str
        docker_user: str = 'root'
        env_file: str = 'env'
        secrets_file: str = 'secrets'
        production = False
        extends: List[str]

    cfg: Config = Config()

    def __init__(self, root_path: str, name: str, stack_config: dict):
        self.name: str = name
        self.root_path: str = root_path
        self.env_path: str = os.path.join(self.root_path, self.name)
        self.stack_base_name: str = stack_config.get('basename', None)
        self._services: Dict = {}
        self._stack_files: List = []
        self._secret_files: List = []
        self._env_files: List = []
        configuration = stack_config['environments'][self.name]

        self.cfg.extends = configuration.get('extends', [])
        if type(self.cfg.extends) == str:
            self.cfg.extends = [self.cfg.extends]
        self.bases = []
        for extendEnv in self.cfg.extends:
            logger.debug("Extending base env '{}' from env '{}'".format(extendEnv, name))
            temp_env = Environment(root_path, extendEnv, stack_config)
            self.bases.append(temp_env)

        self.cfg.stack_name = configuration.get('stack_name', None) or '{}-{}'.format(self.stack_base_name, self.name)
        self.cfg.docker_host = configuration.get('docker_host', None)
        self.cfg.docker_user = configuration.get('docker_user', 'root')
        self.cfg.production = parse_yaml_bool(configuration.get('production', False)) or self.name in ['prod', 'production']

        self._hydrate()

    def _hydrate(self):
        for base in self.bases:
            # logger.debug("Processing base '{}'".format(base.name))
            for fp in base._stack_files:
                self._add_stack_file(fp)
            # print(base._secret_files)
            for fp in base._secret_files:
                self._add_secrets_file(fp)
            # print(base._env_files)
            for fp in base._env_files:
                self._add_env_file(fp)
        self._add_stack_file(os.path.join(self.env_path, 'docker-compose.yml'))
        self._add_secrets_file(os.path.join(self.env_path, self.cfg.secrets_file))
        self._add_env_file(os.path.join(self.env_path, self.cfg.env_file))
        logger.debug("Env '{}' hydrated".format(self.name))

    def _add_secrets_file(self, filepath: str):
        self._secret_files.append(filepath)

    def _add_env_file(self, filepath: str):
        self._env_files.append(filepath)

    def _add_stack_file(self, stack_file: str):
        data = load_required_yaml(stack_file)
        for service_name, service_def in data['services'].items():
            self._services[service_name] = service_def
        self._stack_files.append(stack_file)

    def build_compose_override_list(self):
        res = ''
        for stack_file in self._stack_files:
            res += '-f {} '.format(stack_file)
        return res

    def build_stack_override_list(self):
        res = ''
        for stack_file in self._stack_files:
            res += '-c {} '.format(stack_file)
        return res

    def get_env_files_list(self):
        return self._secret_files + self._env_files

    def ensure_has_service(self, service: str):
        if not self.has_service(service):
            logger.error('No such service')
            exit(1)

    def has_service(self, service: str):
        return service in self._services

    def get_services(self):
        return self._services.keys()

    def get_full_service_name(self, service: str):
        return "{}_{}".format(self.cfg.stack_name, service)
