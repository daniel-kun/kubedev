# kubedev

DevOps command line tool that standardizes workflows for Microservices in Kubernetes for teams: Build, Develop, CI/CD.

It builds on:

- [docker](https://docker.com/)
- [tilt](https://tilt.dev/)
- [helm](https://helm.sh/)
- CI providers:
  - [GitLab](https://gitlab.com/)

## kubedev Principles

- `kubedev` wants to help you quickly and easily build microservices that are independent, but at the same time follow a common pattern in regards to building, documenting and deploying. This makes it easier to add new services, and to onboard new developers.
- `kubedev` aims to be a thin wrapper around the commands it builds on, and just wants to make it easier for teams to call them appropriately.
- `kubedev` always prints the commands that it executes, so that you know what is going on.
- `kubedev` heavily relies on environment variables for service configuration.

## Current state of development

`kubedev` is in early development. Currently, the following commands are implemented:

- _None yet_

## Synopsis

`kubedev` commands are based on the definitions found in `kubedev.json`, which include the minimum necessary information that is required to execute common cloud-dev related tasks.

A kubedev.json describes an "App", which in turn can contain "Sub-Apps" that may be deployments, daemonsets or cronjobs.

Schema of kubedev.json:

```jsonc
{
    "name": "myservice",
    "ci-provider": "gitlab",
    "deployments": {
        "mydeploy": { # A Sub-App `mydeploy' of type deployment
            "used-frameworks": ["python", "pipenv", "npm", "vue"], # used-frameworks are used to e.g. fill in Tiltfile live_update, ignore, etc.
            "dev-only": true, # default: false. Specifies whether this service must only be deployed on local development machines
            "port": 5000,
            "dev-port": 8081, # The port that tilt  up forwards
            "required-envs": {
                "MYDEPLOY_FLASK_ENV": {
                    "documentation": "...",
                    "encoding": "base64"
                }
            }
        }
    },
    "daemonsets": {
       …
    },
    "cronjobs": {
        "mycronjob": {  # A Sub-App mycronjob of type cronjobs
            … # Includes necessary definitions for CronJobs
        }
    }
}
```

## kubedev init [<deployment:name>, …][<cronjob:name>, …] [<daemonset:name>, …]

_NOT IMPLEMENTED, YET_

Creates:

- Directories for each deployment, daemonset or cronjob
- Empty Dockerfiles in these directories
- A template kubedev.json
- A README.md template

## kubedev generate [--overwrite]

_NOT IMPLEMENTED, YET_

Creates a helm-chart (with Deployment/DaemonSet/CronJob and optionally Services), Tiltfile and .gitlab-ci.yml from the definitions in ./kubedev.json. If ./kubedev.json does not exist, instructions are printed (referencing the "kubedev init" command).

## kubedev generate helm-chart \<template\>

_NOT IMPLEMENTED, YET_

Creates a helm-chart for this service, according to kubedev.json, consisting of:

- A Chart.yaml
- A deployment, daemonset or a cronjob, depending on "type".
- For deployments and daemonsets: Adds a Service (type ClusterIP).

## kubedev generate Tiltfile \<template\>

_NOT IMPLEMENTED, YET_

Creates a Tiltfile with some sensible defaults.

## kubedev generate gitlab-ci

_NOT IMPLEMENTED, YET_

Creates a .gitlab-ci.yml file containing the `build-push` and `deploy` states:

- build-push: Runs `kubedev` build and then `kubedev push`
- deploy: Runs `kubedev deploy`

It uses the latest stable dev-baseimage.

## kubedev check

_NOT IMPLEMENTED, YET_

Reads kubedev.json and checks whether all environment variables from the configuration is set in the current environment. It prints missing variables, including it's documentation.

For used-frameworks "pipenv", it runs `bandit`.
For used-frameworks "npm", it runs `npm audit`.

## kubedev print env-doc

_NOT IMPLEMENTED, YET_

Prints out a Markdown table with all environment variables declared in kubedev.json and their documentation.

## kubedev up [--clean]

_NOT IMPLEMENTED, YET_

Checks the current environment and runs `tilt up` when the configuration is OK.

For "used-frameworks" "vue", it runs `npm run build -- --watch --mode development` in parallel.

The --clean switch runs `tilt down` before running tilt up.

## kubedev down

_NOT IMPLEMENTED, YET_

Runs `tilt down`.

## kubedev test-ci \<job\>

_NOT IMPLEMENTED, YET_

Creates a temporary branch, commits all local changes and uncommited files to this branch, then runs `gitlab-runner exec shell <job>` and then restores the previous git state.

## kubedev build \<sub-app\>

_NOT IMPLEMENTED, YET_

Runs `docker build` with all docker build args as defined in kubedev.json and tags it with a temporary, unique development tag.

The docker image name is deducted from the git repository name, thus this command must be run in a git working copy.

Is used inside the CI/CD build jobs.

## kubedev push \<sub-app\>

_NOT IMPLEMENTED, YET_

When `kubedev build` has been run before, it runs `docker push` with the last successful build's unique development tag.

The docker image name is deducted from the git repository name, thus this command must be run in a git working copy.

Is used inside the CI/CD build jobs.

## kubedev run-local [args…]

_NOT IMPLEMENTED, YET_

Runs `kubedev build` and runs the new docker image with all envs set and ports forwarded, optionally with [args…].

## kubedev deploy

_NOT IMPLEMENTED, YET_

Reads the `.kube/conf` from an environment variable, auto-increases the `helm-chart/Chart.yaml`'s version and then runs `helm install` with appropriate arguments and env vars from `kubedev.json`.

Is used inside the CI/CD build jobs.

## kubedev template

_NOT IMPLEMENTED, YET_

Basically runs `helm template` with appropriate arguments and env vars from `kubedev.json`.

Is used inside the Tiltfile.
