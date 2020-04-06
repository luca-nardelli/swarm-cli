from typing import List

import click

from swarm_cli.lib import SwarmModeState, load_env_files, run_cmd


@click.group()
@click.option('--environment', '-e', multiple=True, required=False)
@click.pass_context
def swarm(ctx: click.Context, environment: List[str]):
    load_env_files(environment)
    state = SwarmModeState()
    state.initFromFile('swarm-config.yml')
    ctx.obj = state


@swarm.group()
@click.pass_context
def preset(ctx: click.Context):
    state: SwarmModeState = ctx.obj


@preset.command('ls')
@click.option('--preset', '-p', help="Select a preset", required=False)
@click.pass_context
def preset_ls(ctx: click.Context, preset: str):
    state: SwarmModeState = ctx.obj
    if preset:
        state.ensure_preset(preset)
        for k, v in state.cfg['presets'][preset]['stacks'].items():
            click.secho("{}:{}".format(k, v['variant']))
    else:
        for preset in state.cfg['presets'].keys():
            click.secho("Preset {}".format(preset))
            for k, v in state.cfg['presets'][preset]['stacks'].items():
                click.secho("  - {}:{}".format(k, v['variant']))


@preset.command('deploy')
@click.option('--preset', '-p', help="Select a preset", required=True)
@click.option('--dry-run', is_flag=True)
@click.pass_context
def preset_deploy(ctx: click.Context, preset: str = None, dry_run=False):
    state: SwarmModeState = ctx.obj
    state.ensure_preset(preset)
    preset_data = state.cfg['presets'][preset]
    load_env_files(preset_data.get('env_files', []), ignore_missing=True)
    stacks = state.cfg['presets'][preset]['stacks']
    for k, v in stacks.items():
        name, variant = k, v['variant']
        cmd = ' '.join(['docker', 'stack', 'deploy', state.build_deploy_sequence_for_stack(name, variant), name])
        run_cmd(cmd, dry_run=dry_run, env=state.get_environment_for_stack(preset, name, variant))


@preset.command('build')
@click.option('--preset', '-p', help="Select a preset", required=True)
@click.option('--dry-run', is_flag=True)
@click.pass_context
def preset_build(ctx: click.Context, preset: str = None, dry_run=False):
    state: SwarmModeState = ctx.obj
    state.ensure_preset(preset)
    preset_data = state.cfg['presets'][preset]
    load_env_files(preset_data.get('env_files', []), ignore_missing=True)
    stacks = state.cfg['presets'][preset]['stacks']
    for k, v in stacks.items():
        name, variant = k, v['variant']
        state.prepare_build_folder(preset, name, variant)
        cmd = ' '.join(['docker-compose', state.build_compose_sequence_for_stack(name, variant), 'build'])
        run_cmd(cmd,
                dry_run=dry_run,
                cwd=state.get_build_folder(preset, name, variant),
                env=state.get_environment_for_stack(preset, name, variant)
                )

@preset.command('push')
@click.option('--preset', '-p', help="Select a preset", required=True)
@click.option('--dry-run', is_flag=True)
@click.pass_context
def preset_push(ctx: click.Context, preset: str = None, dry_run=False):
    state: SwarmModeState = ctx.obj
    state.ensure_preset(preset)
    preset_data = state.cfg['presets'][preset]
    load_env_files(preset_data.get('env_files', []), ignore_missing=True)
    stacks = state.cfg['presets'][preset]['stacks']
    for k, v in stacks.items():
        name, variant = k, v['variant']
        cmd = ' '.join(['docker-compose', state.build_compose_sequence_for_stack(name, variant), 'push'])
        run_cmd(cmd,
                dry_run=dry_run,
                env=state.get_environment_for_stack(preset, name, variant)
                )

# @swarm.group()
# def stack():
#     pass
#
#
# @stack.command('ls')
# @click.pass_context
# def stack_ls(ctx: click.Context):
#     state: SwarmModeState = ctx.obj
#     click.echo('Available stacks:')
#     for stack_name in sorted(state.layered_stacks.keys()):
#         click.echo(stack_name)
#         for stack_variant in sorted(state.layered_stacks[stack_name].keys()):
#             click.echo("\t {}".format(stack_variant))
#
#
# @stack.command('deploy')
# @click.argument('name_variant', nargs=-1)
# @click.option('--dump-cmd', is_flag=True)
# @click.pass_context
# def stack_deploy(ctx: click.Context, name_variant: str, dump_cmd: str):
#     state: SwarmModeState = ctx.obj
#     for name_variant_elem in name_variant:
#         name, variant = name_variant_elem.split(':')
#         state.ensure_stack_exists(name, variant)
#         cmd = ' '.join(['docker', 'stack', 'deploy', state.build_deploy_sequence_for_stack(name, variant), name])
#         env = state.get_environment_for_stack(preset, name, variant)
#         run_cmd(cmd, dry_run=dump_cmd, env=env)
#
#
# @stack.command('setup')
# @click.argument('name_variant', nargs=-1)
# @click.option('--dump-cmd', is_flag=True)
# @click.pass_context
# def stack_setup(ctx: click.Context, name_variant: str, dump_cmd: str):
#     state: SwarmModeState = ctx.obj
#     for name_variant_elem in name_variant:
#         name, variant = name_variant_elem.split(':')
#         state.ensure_stack_exists(name, variant)
#         state.ensure_preconditions(name, variant, dump_cmd=dump_cmd)
