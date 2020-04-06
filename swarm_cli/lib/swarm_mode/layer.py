import glob
import os
from typing import List

import click

from swarm_cli.lib.logging import logger
from swarm_cli.lib.swarm_mode.stack import Stack


class Layer:
    root_path: str
    name: str

    stacks: List[Stack] = []

    def __init__(self, name: str, root_path: str = None):
        if root_path:
            self.load_from_path(root_path)

    def load_from_path(self, root_path):
        self.root_path = root_path
        stack_files = glob.glob(os.path.join(root_path, '**/*.stack.yml'), recursive=True)
        for filepath in stack_files:
            stack = Stack(stack_file=filepath)
            logger.verbose('\tLoaded stack {}:{}'.format(stack.name, stack.variant))
            self.stacks.append(stack)

    def get_stack(self, name, variant):
        for stack in self.stacks:
            if stack.name == name and stack.variant == variant:
                return stack
        return None
