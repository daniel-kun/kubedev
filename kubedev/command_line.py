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

from .kubedev import Kubedev, RealEnvAccessor, RealFileAccessor, RealPrinter


def add_common_arguments(argParser):
  argParser.add_argument(
      '-c', '--config', help='Path to config file', required=False, default='kubedev.json')


def main_impl(argv, env_accessor=RealEnvAccessor(), printer=RealPrinter(), file_accessor=RealFileAccessor()):
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

  auditArgParser = argparse.ArgumentParser()
  add_common_arguments(auditArgParser)

  checkArgParser = argparse.ArgumentParser()
  add_common_arguments(checkArgParser)
  checkArgParser.add_argument('command', metavar='Command', type=str, nargs='*',
                              help="An optional sub-command to check for. If provided, only the required environment for this sub-command will be checked.")

  runArgParser = argparse.ArgumentParser()
  add_common_arguments(runArgParser)
  runArgParser.add_argument('container', metavar='Container', type=str,
                             help="The name of the deployment to run locally.")

  systemTestArgParser = argparse.ArgumentParser()
  add_common_arguments(systemTestArgParser)
  systemTestArgParser.add_argument('app', metavar='App', type=str,
                             help="The name of the app to run the system tests for.")

  def print_help(argv):
    print('HELP: TODO')

  def bool_to_returncode(boolValue):
    if boolValue:
      return 0
    else:
      return 1

  def generate(argv):
    args = generatorArgParser.parse_args(argv)
    kubedev = Kubedev()  # TODO: Find templates dir
    return bool_to_returncode(kubedev.generate(args.config))

  def template(argv):
    args = templateArgParser.parse_args(argv)
    kubedev = Kubedev()
    return kubedev.template(args.config)

  def deploy(argv):
    args = deployArgParser.parse_args(argv)
    kubedev = Kubedev()
    return kubedev.deploy(args.config)

  def build(argv):
    args = buildArgParser.parse_args(argv)
    kubedev = Kubedev()
    return kubedev.build(args.config, args.container)

  def push(argv):
    args = pushArgParser.parse_args(argv)
    kubedev = Kubedev()
    return kubedev.push(args.config, args.container)

  def audit(argv):
    args = auditArgParser.parse_args(argv)
    kubedev = Kubedev()
    return kubedev.audit(args.config)

  def check(argv):
    args = checkArgParser.parse_args(argv)
    kubedev = Kubedev()
    return bool_to_returncode(kubedev.check(args.config, args.command,
                         env_accessor=env_accessor, printer=printer, file_accessor=file_accessor))

  def run(argv):
    args = runArgParser.parse_args(argv)
    kubedev = Kubedev()
    return kubedev.run(args.config, args.container,
                         env_accessor=env_accessor, printer=printer, file_accessor=file_accessor)

  def systemTest(argv):
    args = systemTestArgParser.parse_args(argv)
    kubedev = Kubedev()
    return kubedev.system_test(args.config, args.app)

  commands = {
      'generate': generate,
      'template': template,
      'build': build,
      'push': push,
      'deploy': deploy,
      'check': check,
      'audit': audit,
      'run': run,
      'system-test': systemTest,
      'help': print_help
  }

  if len(argv) < 2:
    print_help([])
    return 0
  else:
    command = argv[1]
    if command not in commands:
      print_help(argv[2:])
      return 0
    else:
      return commands[command](argv[2:])


def main():
  return main_impl(sys.argv)
