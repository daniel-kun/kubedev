# kubedev

DevOps command line tool that standardizes workflows for Microservices in Kubernetes for teams: Build, Develop, CI/CD.

`kubedev` is in early development. Currently, the following commands are implemented:

- *None yet*

## Synopsis

`kubedev` commands are based on the definitions found in `kubedev.json`, which include the minimum necessary information that is required to execute common cloud-dev related tasks.

Schema of kubedev.json:

```json
{
    "name": "gcs-service-usagestats",
    "ci-provider": "gitlab",
    "tilt-version": "0.1.20",
    "tilt-version.comment": "The exact tilt version that kubedev uses.",
    "deployments": {
        "usagestats": {
            "used-frameworks": ["python", "pipenv", "npm", "vue"],
            "used-frameworks.comment": "used-frameworks are used to e.g. fill in Tiltfile live_update, ignore, etc.",
            "dev-only": true,
            "dev-only.default": false,
            "dev-only.comment": "Specifies whether this service must only be deployed on local development machines",
            "port": 5000,
            "dev-port": 8081,
            "dev-port.comment": "The port that tilt  up forwards",
            "required-envs": {
                "USAGESTATS_FLASK_ENV": {
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
        "usagestats-transfer": {
            "comment": "Includes necessary definitions for CronJobs".
        }
    }
}
```

## kubedev init [<deployment:name>, …] [<cronjob:name>, …] [<daemonset:name>, …]

*NOT IMPLEMENTED, YET*

Creates:

* Directories for each deployment, daemonset or cronjob
* Empty Dockerfiles in these directories
* A kubedev.json
* A README.md template

## kubedev generate [--overwrite]

*NOT IMPLEMENTED, YET*

Creates a helm-chart (with Deployment/DaemonSet/CronJob and optionally Services), Tiltfile and .gitlab-ci.yml from the definitions in ./kubedev.json. If ./kubedev.json does not exist, instructions are printed (referencing the "kubedev init" command).

In contrast to the `kubedev mk …`-commands, it does not print the files to stdout, but writes them directly, if they do not exist. Otherwise, a warning is printed for each file and the existing file is not modified.

## kubedev generate helm-chart <template>

*NOT IMPLEMENTED, YET*

Creates a helm-chart for this service, according to kubedev.json, consisting of:

- A Chart.yaml
- A deployment, daemonset or a cronjob, depending on "type".
- For deployments and daemonsets: Adds a Service (type ClusterIP).

## kubedev generate Tiltfile <template>

*NOT IMPLEMENTED, YET*

Creates a Tiltfile with some sensible defaults.

## kubedev generate gitlab-ci

*NOT IMPLEMENTED, YET*

Creates a .gitlab-ci.yml file containing the `build-push` and `deploy` states:
- build-push: Runs `kubedev` build and then `kubedev push`
- deploy: Runs `kubedev deploy`

It uses the latest stable dev-baseimage.

## kubedev check

*NOT IMPLEMENTED, YET*

Reads kubedev.json and checks whether all environment variables from the configuration is set in the current environment. It prints missing variables, including it's documentation.

For  used-frameworks "pipenv", it runs `bandit`.
For used-frameworks "npm", it runs `npm audit`.

## kubedev print env-doc

*NOT IMPLEMENTED, YET*

Prints out a Markdown table with all environment variables declared in kubedev.json and their documentation.

## kubedev up [--clean]

*NOT IMPLEMENTED, YET*

Checks the current environment and runs `tilt up` when the configuration is OK.

For "used-frameworks" "vue", it runs `npm run build -- --watch --mode development` in parallel.

The --clean switch runs `tilt down` before running tilt up.

## kubedev down

*NOT IMPLEMENTED, YET*

Runs `tilt down`.

## kubedev test-ci <job>

*NOT IMPLEMENTED, YET*

Creates a temporary branch, commits all local changes and uncommited files to this branch, then runs `gitlab-runner exec shell <job>` and then restores the previous git state.

## kubedev build <subdir>

*NOT IMPLEMENTED, YET*

Runs `docker build` with all docker build args as defined in kubedev.json and tags it with a temporary, unique development tag.

The docker image name is deducted from the git repository name, thus this command must be run in a git working copy.

Is used inside the CI/CD build jobs.

## kubedev push <subdir>

*NOT IMPLEMENTED, YET*

When `kubedev build` has been run before, it runs `docker push` with the last successful build's unique development tag.

The docker image name is deducted from the git repository name, thus this command must be run in a git working copy.

Is used inside the CI/CD build jobs.

## kubedev run-local [args…]

*NOT IMPLEMENTED, YET*

Runs `kubedev build` and runs the new docker image with all envs set and ports forwarded, optionally with [args…].

## kubedev deploy

*NOT IMPLEMENTED, YET*

Reads the `.kube/conf` from an environment variable, auto-increases the `helm-chart/Chart.yaml`'s version and then runs `helm install` with appropriate arguments and env vars from `kubedev.json`.

Is used inside the CI/CD build jobs.

## kubedev template

*NOT IMPLEMENTED, YET*

Does, what currently `gcs-deploy -m template` does, but includes all env vars from kubedev.json.

Is used inside the Tiltfile.
