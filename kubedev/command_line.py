'''
Usage: kubedev <command> [args...]

  Where [args] depend on the command, and the following commands are available:

Commands
  generate      Based on a kubedev.json, generate all files required for the development- and CI/CD-workflow:
                - A helm-chart
                - A Tiltfile
                - A CI-configuration (.gitlab-ci.yml)
                - Directories and Dockerfiles for each defined container
  help          Display this help message            
'''

import argparse
import sys

from .kubedev import Kubedev


def add_common_arguments(argParser):
  argParser.add_argument(
      '-c', '--config', help='Path to config file', required=False, default='kubedev.json')


def main():
  argv = sys.argv
  generatorArgParser = argparse.ArgumentParser()
  add_common_arguments(generatorArgParser)

  templateArgParser = argparse.ArgumentParser()
  add_common_arguments(templateArgParser)

  deployArgParser = argparse.ArgumentParser()
  add_common_arguments(deployArgParser)

  buildArgParser = argparse.ArgumentParser()
  add_common_arguments(buildArgParser)
  buildArgParser.add_argument('container', metavar='Container', type=str,
                              help="The name of the deployment to build the container for.")

  pushArgParser = argparse.ArgumentParser()
  add_common_arguments(pushArgParser)
  pushArgParser.add_argument('container', metavar='Container', type=str,
                             help="The name of the deployment to push the container image for.")

  checkArgParser = argparse.ArgumentParser()
  add_common_arguments(checkArgParser)

  def print_help(argv):
    print('HELP: TODO')

  def generate(argv):
    args = generatorArgParser.parse_args(argv)
    kubedev = Kubedev()  # TODO: Find templates dir
    kubedev.generate(args.config)

  def template(argv):
    args = templateArgParser.parse_args(argv)
    kubedev = Kubedev()
    kubedev.template(args.config)

  def deploy(argv):
    args = deployArgParser.parse_args(argv)
    kubedev = Kubedev()
    kubedev.deploy(args.config)

  def build(argv):
    args = buildArgParser.parse_args(argv)
    kubedev = Kubedev()
    kubedev.build(args.config, args.container)

  def push(argv):
    args = pushArgParser.parse_args(argv)
    kubedev = Kubedev()
    kubedev.push(args.config, args.container)

  def check(argv):
    args = checkArgParser.parse_args(argv)
    kubedev = Kubedev()
    kubedev.check(args.config)

  commands = {
      'generate': generate,
      'template': template,
      'build': build,
      'push': push,
      'deploy': deploy,
      'check': check,
      'help': print_help
  }

  if len(argv) < 2:
    print_help([])
  else:
    command = argv[1]
    if command not in commands:
      print_help(argv[2:])
    else:
      commands[command](argv[2:])
