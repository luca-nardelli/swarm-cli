from typing import Dict, List

from swarm_cli.lib import load_required_yaml
from swarm_cli.lib.logging import logger
from swarm_cli.lib.utils import parse_yaml_bool


class Environment:
    name: str
    base_path: str
    stack_base_name: str
    environment: Dict
    services: Dict = {}
    stack_files: List = []

    class Config:
        stack_name: str
        docker_host: str
        env_file: str = 'env'
        secrets_file: str = 'secrets'
        production = False

    cfg: Config = Config()

    def __init__(self, name: str, stack_base_name: str, configuration: dict):
        self.name = name
        self.stack_base_name = stack_base_name
        self.cfg.stack_name = configuration.get('stack_name', None) or '{}-{}'.format(self.stack_base_name, self.name)
        self.cfg.docker_host = configuration.get('docker_host', None)
        self.cfg.production = parse_yaml_bool(configuration.get('production', False)) or self.name in ['prod', 'production']

    def add_stack_file(self, stack_file: str):
        data = load_required_yaml(stack_file)
        for service_name, service_def in data['services'].items():
            self.services[service_name] = service_def
        self.stack_files.append(stack_file)

    def build_compose_override_list(self):
        res = ''
        for stack_file in self.stack_files:
            res += '-f {}'.format(stack_file)
        return res

    def build_stack_override_list(self):
        res = ''
        for stack_file in self.stack_files:
            res += '-c {}'.format(stack_file)
        return res

    def ensure_has_service(self, service: str):
        if not self.has_service(service):
            logger.error('No such service')
            exit(1)

    def has_service(self, service: str):
        return service in self.services

    def get_services(self):
        return self.services.keys()

    def get_full_service_name(self, service: str):
        return "{}_{}".format(self.cfg.stack_name, service)
