# Copyright (C) 2019 Redis Labs Ltd.
#
# This file is part of mbdirector.
#
# mbdirector is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# mbdirector is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with memtier_benchmark.  If not, see <http://www.gnu.org/licenses/>.

"""
Main module.
"""
import sys
import os.path
import json
import logging
import datetime
import pkg_resources

import click
from jsonschema import validate

from mbdirector.runner import Runner
from mbdirector.serve import run_webserver


def config_logging(log_filename, loglevel):
    formatter = logging.Formatter(
        fmt='%(asctime)s %(levelname)s %(message)s')

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(getattr(logging, loglevel.upper()))


@click.group()
def cli():
    pass


@cli.command()
@click.option('--spec', '-s', required=True, type=click.File('r'),
              help='Benchmark specifications')
@click.option('--loglevel', '-l', default='info',
              type=click.Choice(['debug', 'info', 'error']),
              help='Benchmark specifications')
@click.option('--skip-benchmarks', multiple=True,
              help='Specify benchmarks to skip')
@click.option('--skip-targets', multiple=True,
              help='Specify targets to skip')
def benchmark(spec, loglevel, skip_benchmarks, skip_targets):
    schema_file = pkg_resources.resource_filename(
        'mbdirector', 'schema/mbdirector_schema.json')
    try:
        schema = json.load(open(schema_file))
    except Exception as err:
        click.echo('Error: failed to load schema: {}'.format(err))
        sys.exit(1)

    try:
        spec_json = json.load(spec)
    except Exception as err:
        click.echo('Error: failed to spec: {}: {}'.format(
            spec.name, err))
        sys.exit(1)

    try:
        validate(spec_json, schema)
    except Exception as err:
        click.echo('Error: invalid test: {}: {}'.format(spec.name, err))
        sys.exit(1)

    base_results_dir = os.path.join(
        'results', '{}Z'.format(datetime.datetime.utcnow().isoformat()))
    os.makedirs(base_results_dir)
    config_logging(os.path.join(base_results_dir, 'mbdirector.log'),
                   loglevel)

    _runner = Runner(base_results_dir, spec.name, spec_json,
                     skip_benchmarks, skip_targets)
    _runner.run()


@cli.command()
@click.option('--bind', '-b', required=False, default='127.0.0.1',
              help='Address to bind to')
@click.option('--port', '-p', required=False, default=8080,
              help='Port to listen on')
def serve(bind, port):
    run_webserver(bind, port)
