import os
import sys

import click

from swarm_cli.lib import load_env_files, run_cmd
from swarm_cli.lib.docker_utils import get_first_running_container_for_service
from swarm_cli.lib.logging import logger
from swarm_cli.lib.stack_mode.stack_mode_state import StackModeState


@click.group()
@click.pass_context
@click.option('--env', type=str, default='dev')
def stack(ctx: click.Context, env: str = 'env'):
    state = StackModeState()
    state.initFromFile('stack-config.yml')
    state.selectEnv(env)
    ctx.obj = state
    pass


@stack.command()
@click.pass_context
def ls(ctx: click.Context):
    state: StackModeState = ctx.obj
    click.secho("Available services:")
    for service in sorted(state.current_env.services.keys()):
        click.secho("{}".format(service))


@stack.command()
@click.pass_context
@click.argument('service')
def logs(ctx: click.Context, service: str):
    state: StackModeState = ctx.obj
    state.current_env.ensure_has_service(service)

    client = state.get_docker_client()
    fqsn = state.current_env.get_full_service_name(service)
    docker_container = get_first_running_container_for_service(client, fqsn=fqsn)
    if docker_container:
        for log in docker_container.logs(follow=True, stream=True):
            decoded: str = log.decode("utf-8")
            decoded = decoded.rstrip()
            click.secho(decoded)


def _build(state: StackModeState, dry_run=False):
    load_env_files([
        os.path.join(state.current_env.base_path, state.current_env.cfg.secrets_file),
        os.path.join(state.current_env.base_path, state.current_env.cfg.env_file),
    ], ignore_missing=True)
    env = os.environ.copy()
    if 'DOCKER_HOST' in env:
        del env['DOCKER_HOST']
    cmd = 'docker-compose {} build'.format(state.current_env.build_compose_override_list())
    run_cmd(cmd, dry_run=dry_run, env=env)


def _push(state: StackModeState, dry_run=False):
    load_env_files([
        os.path.join(state.current_env.base_path, state.current_env.cfg.secrets_file),
        os.path.join(state.current_env.base_path, state.current_env.cfg.env_file),
    ], ignore_missing=True)
    env = os.environ.copy()
    if 'DOCKER_HOST' in env:
        del env['DOCKER_HOST']
    cmd = 'docker-compose {} push'.format(state.current_env.build_compose_override_list())
    run_cmd(cmd, dry_run=dry_run, env=env)


def _deploy(state: StackModeState, dry_run=False):
    load_env_files([
        os.path.join(state.current_env.base_path, state.current_env.cfg.secrets_file),
        os.path.join(state.current_env.base_path, state.current_env.cfg.env_file),
    ], ignore_missing=True)
    cmd = 'docker stack deploy {} {} --with-registry-auth'.format(state.current_env.build_stack_override_list(), state.current_env.cfg.stack_name)
    run_cmd(cmd, dry_run=dry_run)


@stack.command()
@click.option('--dry-run', is_flag=True)
@click.pass_context
def build(ctx: click.Context, dry_run=False):
    state: StackModeState = ctx.obj
    _build(state, dry_run)


@stack.command()
@click.option('--dry-run', is_flag=True)
@click.pass_context
def push(ctx: click.Context, dry_run=False):
    state: StackModeState = ctx.obj
    _push(state, dry_run)


@stack.command()
@click.option('--dry-run', is_flag=True)
@click.pass_context
def deploy(ctx: click.Context, dry_run=False):
    state: StackModeState = ctx.obj
    _deploy(state, dry_run)


@stack.command()
@click.option('--dry-run', is_flag=True)
@click.pass_context
def bpd(ctx: click.Context, dry_run=False):
    state = ctx.obj
    _build(state, dry_run)
    _push(state, dry_run)
    _deploy(state, dry_run)


@stack.command()
@click.argument('service')
@click.argument('cmd', required=False)
@click.pass_context
def sh(ctx: click.Context, service: str, cmd: str = None):
    state: StackModeState = ctx.obj
    state.current_env.ensure_has_service(service)

    client = state.get_docker_client()
    fqsn = state.current_env.get_full_service_name(service)
    docker_container = get_first_running_container_for_service(client, fqsn=fqsn)
    if docker_container:
        logger.notice('Attaching to \'{}\''.format(docker_container.id))
        if cmd:
            sys.exit(run_cmd("docker exec -ti \"{}\" sh -c '{}'".format(docker_container.id, cmd)))
        else:
            sys.exit(run_cmd("docker exec \"{}\" sh".format(docker_container.id)))
    else:
        logger.error('No running container found')


@stack.command(name='exec')
@click.argument('service')
@click.argument('cmd')
@click.pass_context
def execCmd(ctx: click.Context, service: str, cmd: str):
    state: StackModeState = ctx.obj
    state.current_env.ensure_has_service(service)

    client = state.get_docker_client()
    fqsn = state.current_env.get_full_service_name(service)
    docker_container = get_first_running_container_for_service(client, fqsn=fqsn)
    if docker_container:
        logger.notice('Attaching to \'{}\''.format(docker_container.id))
        sys.exit(run_cmd("docker exec -ti \"{}\" \"{}\"".format(docker_container.id, cmd)))
    else:
        logger.error('No running container found')
