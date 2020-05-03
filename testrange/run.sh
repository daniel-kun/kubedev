rm -rf Tiltfile helm-chart .gitlab-ci.yml foo-deploy
PYTHONPATH=/home/daniel/projects/kubedev/ python -m kubedev generate -c ../tests/kubedev.spec.json
