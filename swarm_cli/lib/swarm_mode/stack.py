import os

from swarm_cli.lib.utils import load_required_yaml, parse_stack_filename


class Stack:
    root_path: str
    name: str
    variant: str
    docker_stack_file = 'docker-compose.yml'
    files_dir = 'files'

    docker_stack_def: dict

    def __init__(self, stack_file=None):
        if stack_file:
            self.load_from_path(stack_file)

    def load_from_path(self, stack_file):
        self.root_path = os.path.dirname(stack_file)
        self.name, self.variant = parse_stack_filename(os.path.basename(stack_file).replace('.stack.yml', ''))
        data = load_required_yaml(stack_file)
        if data is not None:
            self.name = data.get('name', self.name)
            self.variant = data.get('variant', self.variant)
            self.docker_stack_file = data.get('stack_file', self.docker_stack_file)
            self.files_dir = data.get('files_dir', self.files_dir)
        self.docker_stack_def = load_required_yaml(os.path.join(self.root_path, self.docker_stack_file))

    def get_external_overlay_networks(self):
        res = []
        networks = self.docker_stack_def.get('networks', {})
        for network_name in networks.keys():
            if networks[network_name].get('external', False):
                res.append(network_name)
        return res
