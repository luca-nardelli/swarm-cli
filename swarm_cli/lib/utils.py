import os
import subprocess
import sys
from typing import Union

import click
import yaml

from swarm_cli.lib.logging import logger


def load_required_yaml(path: str):
    if not os.path.exists(path):
        click.secho('Error: file {} not found'.format(path), bold=True, fg='red')
        os._exit(1)
    with open(path, 'r') as infile:
        data = yaml.safe_load(infile)
        return data


def load_env_val(k: str, v: str, overwrite_existing=False):
    if k in os.environ:
        if overwrite_existing:
            logger.spam("Setting {}={}".format(k, v))
            os.environ[k] = v
    else:
        logger.spam("Setting {}={}".format(k, v))
        os.environ[k] = v


def load_env_dict(data: dict, overwrite_existing=False):
    for k, v in data.items():
        load_env_val(k, v, overwrite_existing=overwrite_existing)


def load_env_files(files: list, ignore_missing=False):
    for filepath in files:
        if not os.path.exists(filepath):
            if ignore_missing:
                logger.debug("Loading {}: not found".format(filepath))
                continue
            else:
                logger.error('Can\'t open env file {}'.format(filepath))
                exit(1)
        # Have the shell parse the file for us
        logger.debug("Loading {}".format(filepath))
        cmd = 'env -i sh -c "set -a && . ./{} && env"'.format(filepath)
        res = subprocess.run(cmd, cwd=os.getcwd(), shell=True, env=os.environ, capture_output=True)
        for line in res.stdout.decode().splitlines():
            k, v = line.split('=', maxsplit=1)
            # Ignore PWD as it is always there
            if k == 'PWD':
                continue
            load_env_val(k, v, overwrite_existing=False)


def parse_stack_filename(path: str):
    filename = os.path.basename(path)
    stack_name, stack_variant = filename.split('_')
    return stack_name, stack_variant
    # return {'stack_name': parts[0], 'stack_variant': parts[1]}


def run_cmd(cmd: str, dry_run=False, cwd: str = os.getcwd(), env=os.environ) -> int:
    logger.verbose("+ " + cmd)
    if not dry_run:
        res = subprocess.run(cmd, stdin=sys.stdin, stderr=sys.stderr, stdout=sys.stdout, cwd=cwd, shell=True, env=env)
        return res.returncode
    return 0


def parse_yaml_bool(value: Union[bool, str]):
    if isinstance(value, str):
        return value.lower() in ['true', '1', 't', 'y', 'yes']
    else:
        return value
