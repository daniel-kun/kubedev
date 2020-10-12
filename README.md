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

`kubedev` is in early development. Some commands are implemented (see below), but the test coverage is not
high and there might be some quirks and undocumented behaviour.

## Synopsis

`kubedev` commands are based on the definitions found in `kubedev.json`, which include the minimum necessary information that is required to execute common cloud-dev related tasks.

A kubedev.json describes an "Service", which in turn can contain "Apps" that may be deployments, daemonsets or cronjobs.

Schema of kubedev.json:

```jsonc
{
    "name": "myservice",
    "description": "My fancy service 🎆",
    "imagePullSecrets": "foo-creds", # Your docker registry auth credentials
    "imageRegistry": "foo-registry", # Your docker registry
    "polaris-config": "/path/to/polaris-config.yaml", # specify a custom configuration file for polaris audits
    "required-envs": {
      "MYSERVICE_ENV": {
        "documentation": "Describe MYSERVICE_ENV here, so that other devs on your team know how to set them in their own env",
        "container": true, # Use this environment variable when running containers
        "build": true # Use this environment variable for building the container
      }
    },
    "deployments": {
        "mydeploy": { # An App `mydeploy' of type deployment
            "used-frameworks": ["python", "pipenv", "npm", "vue"], # Not implemented, yet. used-frameworks are used to e.g. fill in Tiltfile live_update, ignore, etc.
            "ports": {
              "https": {
                  "container": "8081", # This is the port that your actual dockerized service is bound to
                  "service": "8082",   # This is the port that the Kubernetes service serves on. Will be redirected to the container-port of the pods.
                  "dev": "8083" # This is the port used for local development by either `tilt` or `kubedev run`. Will be available on localhost when using `tilt up` or `kubedev run`.
              }
            },
            "mounts": {
              "dev": {
                "host_path": "/container/path" # Mount local directories to container directories when running via `kubedev run`
              }
            },
            "required-envs": {
                "MYDEPLOY_FLASK_ENV": {
                    "documentation": "..."
                }
            }
        }
    },
    "daemonsets": {
       # … not implemented, yet
    },
    "cronjobs": {
       # … not implemented, yet
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

✔ Implemented

Creates a helm-chart (with Deployment and optionally Services), Tiltfile, .gitlab-ci.yml and Dockerfiles and probably subdirectories for each App from the definitions in ./kubedev.json. If ./kubedev.json does not exist, instructions are printed (referencing the "kubedev init" command).

## kubedev generate helm-chart \<template\>

❌ _NOT IMPLEMENTED, YET_

Creates a helm-chart for this service, according to kubedev.json, consisting of:

- A Chart.yaml
- A deployment, daemonset or a cronjob, depending on "type".
- For deployments and daemonsets: Adds a Service (type ClusterIP).

## kubedev generate Tiltfile \<template\>

❌ _NOT IMPLEMENTED, YET_

Creates a Tiltfile with some sensible defaults.

## kubedev generate gitlab-ci

❌ _NOT IMPLEMENTED, YET_

Creates a .gitlab-ci.yml file containing the `build-push` and `deploy` states:

- build-push: Runs `kubedev` build and then `kubedev push`
- deploy: Runs `kubedev deploy`

It uses the latest stable dev-baseimage.

## kubedev check

Reads kubedev.json and checks whether all environment variables from the configuration is set in the current environment. It prints missing variables, including it's documentation.

❌ __ NOT IMPLEMENTED:__

For used-frameworks "pipenv", it runs `bandit`.
For used-frameworks "npm", it runs `npm audit`.

## kubedev print env-doc

❌ _NOT IMPLEMENTED, YET_

Prints out a Markdown table with all environment variables declared in kubedev.json and their documentation.

## kubedev up [--clean]

❌ _NOT IMPLEMENTED, YET_

Checks the current environment and runs `tilt up` when the configuration is OK.

For "used-frameworks" "vue", it runs `npm run build -- --watch --mode development` in parallel.

The --clean switch runs `tilt down` before running tilt up.

## kubedev down

❌ _NOT IMPLEMENTED, YET_

Runs `tilt down`.

## kubedev test-ci \<job\>

❌ _NOT IMPLEMENTED, YET_

Creates a temporary branch, commits all local changes and uncommited files to this branch, then runs `gitlab-runner exec shell <job>` and then restores the previous git state.

## kubedev build \<app\>

✔ Implemented

Runs `docker build` for \<app\> with all docker build args as defined in kubedev.json. When CI_COMMIT_SHORT_SHA and CI_COMMIT_REF_NAME are set (inside a GitLab CI build job), the tag will be formatted as "${CI_COMMIT_SHORT_SHA}_${CI_COMMIT_REF_NAME}", otherwise the tag will be "none".

Is used inside the CI/CD build jobs generated by `kubedev generate` and internally by the `kubedev run` command.

## kubedev push \<app\>

✔ Implemented

Runs `docker push` for \<app\>. When CI_COMMIT_SHORT_SHA and CI_COMMIT_REF_NAME are set (inside a GitLab CI build job), the tag will be formatted as "${CI_COMMIT_SHORT_SHA}_${CI_COMMIT_REF_NAME}", otherwise the tag will be "none".

Is used inside the CI/CD build jobs generated by `kubedev generate`.

## kubedev run \<app\>

✔ Implemented

Runs `kubedev build` and then runs the new docker image with all envs set and ports forwarded.

## kubedev deploy

✔ Implemented

Reads a kube config from the env var $KUBEDEV_KUBECONFIG (required) and optionally a context from $KUBEDEV_KUBECONTEXT and then runs `helm upgrade --install` with appropriate arguments and env vars from `kubedev.json`.

Is used inside the CI/CD build jobs generated by `kubedev generate`.

## kubedev template

Basically runs `helm template` with appropriate arguments and env vars from `kubedev.json`.

Is used inside the Tiltfile generated by `kubedev generate`.
