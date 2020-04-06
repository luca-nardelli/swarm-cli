#! /bin/env python3
import logging
import os
import subprocess
import sys
from io import StringIO
from typing import List

import click
import verboselogs
from dotenv import load_dotenv

from swarm_cli import cli_stack
from swarm_cli.cli_swarm import swarm
from swarm_cli.lib.logging import logger
from .lib import SwarmModeState


@click.group()
@click.option('-v', '--verbose', count=True)
@click.pass_context
def root(ctx: click.Context, verbose: int):
    if verbose == 0:
        logger.setLevel(logging.INFO)
    if verbose == 1:
        logger.setLevel(verboselogs.VERBOSE)
    if verbose == 2:
        logger.setLevel(logging.DEBUG)
    if verbose == 3:
        logger.setLevel(verboselogs.SPAM)
    pass


@root.command()
def printenv():
    # for a in sorted(os.environ):
    #     click.secho('{}={}'.format(a, os.getenv(a)))
    res = subprocess.run('printenv | sort', stderr=sys.stderr, stdout=sys.stdout, cwd=os.getcwd(), shell=True)


root.add_command(swarm)
root.add_command(cli_stack.stack)

if __name__ == '__main__':
    root()
