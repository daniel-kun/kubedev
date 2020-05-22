#!/bin/bash

if [ $1 == "generate" ]
then
  echo -e ">>> Cleaning up before re-generating files <<<\n"
  rm -rf Tiltfile helm-chart .gitlab-ci.yml foo-deploy
fi

export KUBEDEV_KUBECONFIG=default
PYTHONPATH="`pwd`/../" python -m kubedev.cli $* -c ../tests/kubedev.spec.json
