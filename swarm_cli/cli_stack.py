import os
import pprint
import sys
from typing import Union, List

import click
import dpath.util

from swarm_cli.lib import load_env_files, run_cmd
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
@click.option('--tail', type=str, default='100')
def logs(ctx: click.Context, service: str, tail: Union[str, int] = '100'):
    state: StackModeState = ctx.obj
    state.current_env.ensure_has_service(service)

    try:
        tail = int(tail)
    except:
        pass

    fqsn = state.current_env.get_full_service_name(service)
    docker_container, client = state.get_first_running_container_for_service(fqsn=fqsn)
    if docker_container:
        for log in docker_container.logs(follow=True, stream=True, tail=tail):
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
@click.option('--dry-run', is_flag=True)
@click.pass_context
def rm(ctx: click.Context, dry_run=False):
    state: StackModeState = ctx.obj
    for service_name in sorted(state.current_env.services.keys()):
        fqsn = state.current_env.get_full_service_name(service_name)
        service = state.get_docker_client().services.get(fqsn)
        click.secho("Removing {} - {}".format(fqsn, service.id))
        service.remove()


@stack.command()
@click.argument('service')
@click.argument('cmd', required=False)
@click.pass_context
def sh(ctx: click.Context, service: str, cmd: str = None):
    state: StackModeState = ctx.obj
    state.current_env.ensure_has_service(service)

    fqsn = state.current_env.get_full_service_name(service)
    docker_container, client = state.get_first_running_container_for_service(fqsn=fqsn)
    if docker_container:
        logger.notice('Attaching to \'{}\''.format(docker_container.id))
        env = os.environ.copy()
        env['DOCKER_HOST'] = client.docker_host
        if 'DOCKER_HOST' in env and env['DOCKER_HOST'] is None:
            del env['DOCKER_HOST']
        if cmd:
            sys.exit(run_cmd("docker exec -ti \"{}\" sh -c '{}'".format(docker_container.id, cmd), env=env))
        else:
            sys.exit(run_cmd("docker exec -ti \"{}\" sh".format(docker_container.id), env=env))
    else:
        logger.error('No running container found')


@stack.command(name='exec')
@click.option('-t', is_flag=True)
@click.option('-i', is_flag=True)
@click.argument('service')
@click.argument('cmd')
@click.argument('other', nargs=-1)
@click.pass_context
def execCmd(ctx: click.Context, service: str, cmd: str, other: List[str], t=False, i=False):
    state: StackModeState = ctx.obj
    state.current_env.ensure_has_service(service)

    fqsn = state.current_env.get_full_service_name(service)
    docker_container, client = state.get_first_running_container_for_service(fqsn=fqsn)
    if docker_container:
        logger.notice('Attaching to \'{}\''.format(docker_container.id))
        env = os.environ.copy()
        env['DOCKER_HOST'] = client.docker_host
        if 'DOCKER_HOST' in env and env['DOCKER_HOST'] is None:
            del env['DOCKER_HOST']
        flags = []
        if t:
            flags.append('-t')
        if i:
            flags.append('-i')
        sys.exit(run_cmd("docker exec {} \"{}\" \"{}\" {}".format(' '.join(flags), docker_container.id, cmd, ' '.join(other)), env=env))
    else:
        logger.error('No running container found')


@stack.command(name='ps')
@click.argument('other', nargs=-1)
@click.pass_context
def ps(ctx: click.Context, other: List[str]):
    state: StackModeState = ctx.obj
    env = os.environ.copy()
    sys.exit(run_cmd("docker stack ps {}".format(state.current_env.cfg.stack_name), env=env))


@stack.command(name='env')
@click.pass_context
def env(ctx: click.Context):
    state: StackModeState = ctx.obj
    load_env_files([
        os.path.join(state.current_env.base_path, state.current_env.cfg.secrets_file),
        os.path.join(state.current_env.base_path, state.current_env.cfg.env_file),
    ], ignore_missing=True)
    pprint.pprint(dict(os.environ), width=1)


@stack.command(name='run')
@click.option('--dry-run', is_flag=True)
@click.argument('cmd', nargs=-1)
@click.pass_context
def run(ctx: click.Context, dry_run=False, cmd: List[str] = []):
    state: StackModeState = ctx.obj
    load_env_files([
        os.path.join(state.current_env.base_path, state.current_env.cfg.secrets_file),
        os.path.join(state.current_env.base_path, state.current_env.cfg.env_file),
    ], ignore_missing=True)
    env = os.environ.copy()
    sys.exit(run_cmd(' '.join(cmd), env=env, dry_run=dry_run))


@stack.command()
@click.argument('services', nargs=-1)
@click.pass_context
def ports(ctx: click.Context, services: List[str]):
    state: StackModeState = ctx.obj
    if len(services) == 0:
        services = state.current_env.get_services()

    client = state.get_docker_client()
    for service in services:
        state.current_env.ensure_has_service(service)
        fqsn = state.current_env.get_full_service_name(service)
        service = client.services.get(fqsn)
        if service:
            ports = dpath.util.values(service.attrs, 'Endpoint/Ports/*')
            if len(ports) > 0:
                print(fqsn)
                for port in ports:
                    print("\t{:>6s}: {:>6s} -> {:6s}".format(str(port['Protocol']), str(port['PublishedPort']), str(port['TargetPort'])))
        else:
            logger.error('No service found')


@stack.command()
@click.argument('services', nargs=-1)
@click.pass_context
def force_update(ctx: click.Context, services: List[str]):
    state: StackModeState = ctx.obj
    for service in services:
        state.current_env.ensure_has_service(service)
        client = state.get_docker_client()
        fqsn = state.current_env.get_full_service_name(service)
        service = client.services.get(fqsn)
        if service:
            print(service.force_update())
        else:
            logger.error('No service found {}'.format(service))
