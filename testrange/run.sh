#rm -rf Tiltfile helm-chart .gitlab-ci.yml foo-deploy
export KUBEDEV_KUBECONFIG=default
PYTHONPATH=/home/daniel/projects/kubedev/ python -m kubedev $* -c ../tests/kubedev.spec.json
