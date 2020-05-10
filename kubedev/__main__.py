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

from kubedev import Kubedev


def add_common_arguments(argParser):
  argParser.add_argument(
      '-c', '--config', help='Path to config file', required=False, default='kubedev.json')


if __name__ == '__main__':
  generatorArgParser = argparse.ArgumentParser()
  add_common_arguments(generatorArgParser)

  templateArgParser = argparse.ArgumentParser()
  add_common_arguments(templateArgParser)

  def print_help(argv):
    print('HELP: TODO')

  def generate(argv):
    args = generatorArgParser.parse_args(argv)
    kubedev = Kubedev('./templates/')  # TODO: Find templates dir
    kubedev.generate(args.config)

  def template(argv):
    args = templateArgParser.parse_args(argv)
    kubedev = Kubedev('./templates/')
    kubedev.template(args.config)

  commands = {
      'generate': generate,
      'template': template,
      'help': print_help
  }

  if len(sys.argv) < 2:
    print_help([])
  else:
    command = sys.argv[1]
    if command not in commands:
      print_help(sys.argv[2:])
    else:
      commands[command](sys.argv[2:])
