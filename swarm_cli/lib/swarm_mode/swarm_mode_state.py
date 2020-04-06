import os
import shutil
import subprocess
import sys
from typing import List, Dict

import click
import docker
from docker import DockerClient

from swarm_cli.lib.logging import logger
from swarm_cli.lib.swarm_mode.layer import Layer
from swarm_cli.lib.swarm_mode.stack import Stack
from swarm_cli.lib.utils import load_required_yaml, load_env_dict


class SwarmModeState:
    layers: List[Layer] = []
    cfg: dict

    layered_stacks: Dict[str, Dict[str, List[Stack]]] = {}

    client: DockerClient

    class CliState:
        selected_preset: str

    cli_state: CliState = CliState()

    def initFromFile(self, path: str):
        data = load_required_yaml(path)
        self.cfg = data

        # Load layers
        self._load_layers(data['layers'])

        # Set base_environment
        load_env_dict(data.get('environment', {}))

    def _get_client(self):
        if not self.client:
            self.client = docker.from_env()
        return self.client

    def _load_layers(self, layers: list):
        for layer_root_path in layers:
            logger.verbose('Parsing layer {}'.format(layer_root_path))
            layer = Layer(os.path.basename(layer_root_path), layer_root_path)

            for stack in layer.stacks:
                variants = self.layered_stacks.get(stack.name, {})
                stacks = variants.get(stack.variant, [])
                stacks.append(stack)
                variants[stack.variant] = stacks
                self.layered_stacks[stack.name] = variants

            self.layers.append(layer)

    def has_preset(self, preset: str):
        return preset in self.cfg.get('presets', {})

    def ensure_preset(self, preset: str):
        if not self.has_preset(preset):
            logger.error('Preset {} does not exist. Check swarm-config.yml'.format(preset))
            exit(1)
        stacks = self.cfg['presets'][preset]['stacks']
        for k, v in stacks.items():
            name, variant = k, v['variant']
            self.ensure_stack_exists(name, variant)

    def ensure_preconditions(self, name=None, variant=None, dump_cmd=False):
        for stack in self.get_layered_stacks(name, variant):
            for network in stack.get_external_overlay_networks():
                cmd = 'docker network create {} -d overlay || true'.format(network)
                if dump_cmd:
                    click.secho(cmd)
                else:
                    res = subprocess.run(cmd, stderr=sys.stderr, stdout=sys.stdout, cwd=os.getcwd(), shell=True)

    def build_deploy_sequence_for_stack(self, name=None, variant=None):
        cmd = ''
        for stack in self.get_layered_stacks(name, variant):
            cmd += '-c {} '.format(os.path.abspath(os.path.join(stack.root_path, stack.docker_stack_file)))
        cmd = cmd.rstrip()
        return cmd

    def build_compose_sequence_for_stack(self, name=None, variant=None):
        cmd = ''
        for stack in self.get_layered_stacks(name, variant):
            cmd += '-f {} '.format(os.path.abspath(os.path.join(stack.root_path, stack.docker_stack_file)))
        cmd = cmd.rstrip()
        return cmd

    def does_stack_exist(self, name: str, variant: str):
        return len(list(self.get_layered_stacks(name, variant))) > 0

    def ensure_stack_exists(self, name: str, variant: str):
        if not self.does_stack_exist(name, variant):
            click.secho("Stack {} {} does not exist".format(name, variant), fg='red')
            exit(1)

    def get_layered_stacks(self, name, variant):
        for layer in self.layers:
            stack = layer.get_stack(name, variant)
            if stack:
                yield stack

    def get_build_folder(self, preset, name, variant):
        root_build_dir = "build/{}/{}/{}".format(preset, name, variant)
        return root_build_dir

    def get_environment_for_stack(self, preset, name, variant, additional_env=None):
        if additional_env is None:
            additional_env = {}
        new_env = os.environ.copy()
        for k, v in self.cfg['presets'][preset].get('environment', {}).items():
            new_env[k] = v
        new_env['STACK_NAME'] = name
        new_env.update(additional_env)
        return new_env

    def prepare_build_folder(self, preset, name, variant):
        stacks = self.get_layered_stacks(name, variant)
        root_build_dir = self.get_build_folder(preset, name, variant)
        shutil.rmtree("{}".format(root_build_dir), ignore_errors=True)
        os.makedirs(root_build_dir, exist_ok=True)
        for stack in stacks:
            files_dir = os.path.join(stack.root_path, 'files')
            if os.path.exists(files_dir):
                shutil.copytree(files_dir, os.path.join(root_build_dir, 'files'), copy_function=os.link)
                logger.debug('Preparing folder {}'.format(files_dir))
