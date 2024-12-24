#!/usr/bin/env python
# -*- coding: utf-8 -*-#
import importlib
import os

import click

from adt.application.config import config, load_yaml
from adt.infrastructure.fabric_utils import CliConnection


@click.command()
@click.option("--script", "-s", default="./script_file.yaml", help="script file path")
@click.option(
    "--config_file", "-c", default="./config_file.yaml", help="config file path"
)
@click.option("--mode", "-m", default="local", help="test mode")
@click.option("--junit_parser_path", "-jp", help="junit parser path")
@click.argument("cmd")
def main(cmd, script, config_file, mode, junit_parser_path):
    package_path, _ = os.path.split(
        importlib.import_module(config.SERVICE_NAME).__file__
    )

    print(
        f"adt::main : parameter check (cmd: {cmd}, script: {script}, config_file: {config_file}, mode: {mode}, "
        f"junit_parser_path: {junit_parser_path})"
    )

    fabfile = "{}/application/fabfile.py".format(package_path)
    options = ""

    if cmd in "it":
        options = f"--script {script} --config_file {config_file} --mode {mode}"
    elif cmd in "deploy":
        options = f":script={script}"
    elif cmd in "rollback":
        pass
        # options = f':script={script}'
    elif cmd in "junit-parser":
        cmd = "junit_parser"
        options = f":path={junit_parser_path}"
    else:
        raise KeyboardInterrupt

    conf_data = load_yaml(script)[config.CONFIG][config.HOST_ENV]
    print(conf_data)
    with CliConnection(
        conf_data[config.HOST], conf_data[config.USER], conf_data[config.PASSWORD]
    ) as c:
        c.local(f"fab2 -r {fabfile} {cmd} {options}")


if __name__ == "__main__":
    main()
