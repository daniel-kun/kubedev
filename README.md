# kubedev

DevOps command line tool that standardizes workflows for Microservices in Kubernetes for teams:

> Develop, Build, Secure, Deploy.

It builds on well-known and field-proven tools:

- [docker](https://docker.com/)
- [tilt](https://tilt.dev/)
- [helm](https://helm.sh/)
- [kind](https://kind.sigs.k8s.io/)
- Security audits:
  - [Fairwinds Polaris](https://github.com/FairwindsOps/polaris)
- CI providers:
  - [GitLab](https://gitlab.com/)

## kubedev Principles

- `kubedev` wants to help you quickly and easily build microservices that are independent, but at the same time follow a common pattern in regards to building, documenting and deploying. This makes it easier to add new services, and to onboard new developers.
- `kubedev` aims to be a thin wrapper around the commands it builds on, and just wants to make it easier for teams to call them appropriately.
- `kubedev` always prints the commands that it executes, so that you know what is going on.
- `kubedev` heavily relies on environment variables for service configuration.
- `kubedev` helps you build your services "secure by default".

## Current state of development

`kubedev` is in early development and used internally at Gira.

## Synopsis

`kubedev` commands are based on the definitions found in `kubedev.json`, which include the minimum necessary information that is required to execute common cloud-dev related tasks.

A kubedev.json describes an "Service", which in turn can contain "Apps" that may be deployments or cronjobs.

Schema of kubedev.json:

```jsonc
{
    "name": "myservice",
    "description": "My fancy service 🎆",
    "imagePullSecrets": "foo-creds", # Your docker registry auth credentials
    "imageRegistry": "foo-registry", # Your docker registry
    "helmReleaseName": "myservice-v1", # An optional name of the helm release. If not specified, 'name' will be used.
    "securityChecks": {
      "polaris": { # Optional, specify a custom polaris configuration
        "configFile": "polaris-config-cli.yaml", # Local file name of the polaris config
        "configDownload": { # Optional, download the polaris config to the local file before running the audit
          "url": "https://url-to-your-polaris-config",
          "headers": { # Optional, specify headers added to the GET request to download the polaris config
            "Authentication": "Bearer ${YOUR_BEARER_TOKEN}"
          }
        }
      }
    },
    "required-envs": {
      "MYSERVICE_ENV": {
        "documentation": "Describe MYSERVICE_ENV here, so that other devs on your team know how to set them in their own env",
        "container": true, # Use this environment variable when running containers
        "build": true # Use this environment variable for building the container
      }
    },
    "deployments": {
        "mydeploy": { # An App `mydeploy' of type deployment
            "usedFrameworks": ["python", "pipenv", "npm", "vue"], # Not implemented, yet. usedFrameworks are used to e.g. fill in Tiltfile live_update, ignore, etc.
            "ports": {
              "https": {
                  "container": "8081", # This is the port that your actual dockerized service is bound to
                  "service": "8082",   # This is the port that the Kubernetes service serves on. Will be redirected to the container-port of the pods.
                  "dev": "8083" # This is the port used for local development by either `tilt` or `kubedev run`. Will be available on localhost when using `tilt up` or `kubedev run`.
              }
            },
            "volumes": {
              "dev": {
                "other_path": "/short/path" # Shorthand to mount a path read-write,
                "host_path": {
                  "path": "/container/path", # Mount local directories to container directories when running via `kubedev run`
                  "readOnly": true # mount them read-only
                },
                "inline_content.txt": {
                  "content": "Hello, World!", # Mount fixed, plain-text content to a file at 'path'
                  "path": "/container/path",
                  "readOnly": true # mount file read-only
                },
                "inline_content_base64.txt": {
                  "path": "/container/path", # Mount fixed, base64-encoded content to a file at 'path'
                  "base64": "SGVsbG8sIFdvcmxkIQ==",
                  "readOnly": true # mount file read-only
                }
              }
            },
            "required-envs": {
                "MYDEPLOY_FLASK_ENV": {
                    "documentation": "..."
                },
                "MYDEPLOY_COMPLEX": {
                  "documentation": "This is a variable with content that can not be passed to the helm chart on the command line and must be base64-encoded.",
                  "transform": "base64"
                }
            },
            # Defines the system test for this app. System tests must be defined in the directory ./systemTests/<app-name>/ and must include a Dockerfile:
            "systemTest": {
                "variables": {
                  # Defines variables that are passed as environment variables into the test container and all services:
                  "TEST_GLOBAL_VAR": "value"
                },
                "testContainer": {
                    "variables": {
                        # Defines environment variables that are passed to the system-test container
                        "TEST_HOSTNAME": "myservice-test"
                    },
                    "buildArgs": {
                        # Defines build arguments for the system test container
                        "TEST_BUILD_X": "X"
                  }
                },
                # Services run in the background, in an isolated docker network, while the system test container is executed
                "services": {
                    # Services can reference deployments defined in this kubedev.json and will use the latest available image tag,
                    # as generated by e.g. `kubedev build`.
                    "{mydeploy}": {
                        "hostname": "myservice-test", # The system test container can access this service by this hostname
                        "ports": [8081], # Ports that are accessible from other containers
                        "variables": {
                            # Environment variables that are passed to this service.
                            # All required-envs for this deployment are passed, too, but can be overwritten here:
                            "MYSERVICE_ENV": "test-value"
                        }
                    },
                    # Services can use public images or images from your private repository, too:
                    "postgres:13": {
                        "hostname": "postgres-test",
                        "ports": [5432], # Ports that are accessible from other containers
                        "variables": {
                            "POSTGRES_USER": "tempuser",
                            "POSTGRES_PASSWORD": "correct horse battery staple"
                        }
                    }
                }
            }
        }
    },
    "cronjobs": {
        "myjob": {
            "volumes": {
              "dev": {
                  "job_files/": "/tmp/job_files/"
              }
            },
            "required-envs": {
                "MYJOB_VAR": {
                    "documentation": "..."
                }
            },
            "systemTests": {
                # See the detailed documentation on system tests below.
                "services": {
                    # Services can use public images or images from your private repository, too:
                    "postgres:13": {
                        "hostname": "postgres-test",
                        "ports": [5432], # Ports that are accessible from other containers
                        "variables": {
                            "POSTGRES_USER": "tempuser",
                            "POSTGRES_PASSWORD": "correct horse battery staple"
                        }
                    }
                }
            }
        }
    }
}
```

## Naming conventions

`kubedev` will work with artifacts that follow certain naming conventions that are built from the \<service name\> (top level "name"), the \<app name\> (the "name" inside of "deployments" and "cronjobs") and a tag, which will be used as the image tag.

|Artifact|Naming Convention|
|--------|-----------------|
|helm chart name|The helm chart is generated with the name `<service name>`.|
|helm release name|The release name is either directly specified using `helmReleaseName` in `kubedev.json`, or is the same as the helm chart name if `helmReleaseName` is not specified.|
|kubernetes labels|All kubernetes definitions include the labels `kubedev-deployment` or `kubedev-cronjob` (\<service name\>) and `kubedev-app` \<app name\>.|
|image name|The image name is built using `<imageRegistry>/<service name>-<app name>`, except when \<app name> is the same as \<service name\>, in which case it is collapsed to just `<imageRegistry>/<app name>`|
|image tag|The tag is either built using `"${CI_COMMIT_SHORT_SHA}_${CI_COMMIT_REF_NAME}"`, if both these environment variables are set, or to `none` otherwise.|

## Automatic docker login

When kubedev needs to access docker registries, it writes the content of `${DOCKER_AUTH_CONFIG}` to the file `${HOME}/.docker/config.json`, if:
- `~/.docker/config.json` does not exist.
- The environment variable `${HOME}` is set.
- The environment variable `${CI}` is set.
- The environment variable `${DOCKER_AUTH_CONFIG}` is set.

## Environment Variable Transformation

Environment Variables are passed to `helm` and `docker` by shell expansion. This has some limitations of values that are not "shell-safe", such as when they contain double-quotes or special characters. To make it safe and possible to pass these values, kubedev provides a few transformations.

A transformation will take the content of the variable from the environment where kubedev is called, and pass it in a transformed way into `helm --set` and `docker --build-arg / --env`.

Available transformations are:

|Transformation|Description|
|--------------|-----------|
|base64|Base64 encodes the value|

You can enable a transformation by setting the attribute `transform` in `required-envs` to the desired transformation, e.g. `base64`.

## kubedev generate

Creates artifacts that kick-starts your microservice development.

The following files are created for by - with secure defaults:

- Tiltfile
- .gitlab-ci.yml
- helm-chart/ with all required kubernetes ressources
- \<your-service\>/Dockerfile

See [Naming Conventions](#naming-conventions).

The following "usedFrameworks" are supported by `kubedev generate`.

### pipenv

When "pipenv" is included in the "usedFrameworks" by either an app or globally, the following files are generated inside the \<app\>'s sub-directory:

|File|Description|
|----|-----------|
|Dockerfile|Includes pipenv-specific instructions|
|app.py|An empty python script|
|Pipfile|A Pipfile using python 3.8. No packages or dev-packages are added.|
|Pipfile.lock|The result of locking the empty Pipfile.|

## kubedev check

Reads kubedev.json and checks whether all environment variables from the configuration is set in the current environment. It prints missing variables, including it's documentation.

## kubedev audit

Audits the k8s specification using [Fairwind's Polaris](https://github.com/FairwindsOps/polaris).

A custom configuration file can be specified via the configuration options `securityChecks.polaris`, see the example.

Possible configuration options:

|JSON field|Description|
|----------|-----------|
|`securityChecks.polaris.configFile`|A path to a local configuration file that is passed to `polaris`. The file must exist or `configDownload` must be specified. Environment variables will be expanded.|
|`securityChecks.polaris.configDownload`|An optional object that can be used to specify a download path where `kubedev audit` will fetch the polaris configuration from.|
|`securityChecks.polaris.configDownload.url`|The URL to the polaris config. Environment variables will be expanded. When the object `configDownload` exists, the field `url` is mandatory.|
|`securityChecks.polaris.configDownload.headers`|An optional dictionary that can contain custom headers that will be passed to the polaris config download. Both the header names and values can include environment variables.|

*Note:* The polaris executable needs to be available in your $PATH.

## kubedev build \<app\>

Runs `docker build` for \<app\> with all docker build args as defined in kubedev.json.

See [Naming Conventions](#naming-conventions).

This commands writes the content of `${DOCKER_AUTH_CONFIG}` to the file `${HOME}/.docker/config.json`, if:
- `~/.docker/config.json` does not exist.
- The environment variable `${CI}` is set.
- The environment variable `{DOCKER_AUTH_CONFIG}` is set.

`kubedev build` is used inside the CI/CD build jobs generated by `kubedev generate` and internally by the `kubedev run` command.

## kubedev push \<app\>

Runs `docker push` for \<app\>.

See [Naming Conventions](#naming-conventions).

See [Automatic docker login](#automatic-docker-login)

`kubedev push` is used inside the CI/CD build jobs generated by `kubedev generate`.

## kubedev run \<app\>

Builds an image using `kubedev build` with a random tag and then runs it.

The following parameters are passed to `docker run`, some of them can be configured in `kubedev.json`:

- `--interactive` and `--rm` are always passed
- If kubedev is called from a terminal, `--tty` is passed.
- `required-envs` are forwarded to the container.
- All `ports.\<port-name\>.dev` will be forwarded to `ports.\<port-name\>.container`
- `volumes.dev` are passed to the container. kubedev will auto-detect a WSL + Docker Desktop environment and convert the source path to a Windows path using `wsl-path -aw`.

## kubedev deploy

Reads a kube config from the env var $KUBEDEV_KUBECONFIG (required), writes it to *\<temp-kubeconfig-file\>* and optionally a context from $KUBEDEV_KUBECONTEXT and then runs `helm upgrade --install --kube-config "<temp-kubeconfig-file>` with appropriate arguments and all required env vars from `kubedev.json`.

See [Naming Conventions](#naming-conventions).

The generated image tag is passed to the template using the environment variable KUBEDEV_TAG.

`kubedev deploy` is used inside the CI/CD build jobs generated by `kubedev generate`.

## kubedev template

Basically runs `helm template` with appropriate arguments and env vars from `kubedev.json`.

See [Naming Conventions](#naming-conventions).

The generated image tag is passed to the template using the environment variable KUBEDEV_TAG.

`kubedev template` is used inside the Tiltfile generated by `kubedev generate`.

## kubedev system-test \<app name\>

### System Tests for Deployments

If \<app-name\> is a deployment, the system-test is run in "deployment"-mode, which is different and much quicker than the "cronjob"-mode (see below).

In "deployment"-mode, a system-test container is run against defined services, which can either be services defined in `kubedev.json`, or services pulled from a registry such as a database or a service defined in another repository. The system-test container and the services run directly in docker and not in Kubernetes.

See [Automatic docker login](#automatic-docker-login)

`kubedev system-test`'s behaviour is defined in a "systemTest" sub-element of the deployment definition. See the thorough example at the beginning of the README.md.

The following configuration options are available:

|Configuration element|Description|Mandatory|
|---------------------|-----------|---------|
|`systemTest.variables`|Defines global variables that are passed as environment variables into the services (if defined) and the system test container|No|
|`systemTest.testContainer.variables`|Defines variables  that are passed as environment variables into the system test container, but not the services|No|
|`systemTest.testContainer.buildArgs`|Defines build args that are used when building the system test container|No|
|`systemTest.testContainer.services`|Defines services that are run in the background when running the system test container. Use the syntax `{\<app name\>` to reference deployments that are defined in this `kubedev.json`, and the image name will be built automatically according to the same rules are `kuebdev build` would. The app's `volumes.dev` are passed to the container as `kubedev run` does.|No|
|`systemTest.testContainer.services[...].hostname`|This service will be available by this hostname from the system test container|Yes|
|`systemTest.testContainer.services[...].ports`|Defines ports that are published from this service|No|
|`systemTest.testContainer.services[...].variables`|Defines additional environment variables that are passed to this service. When this service references a kubedev deployment, additionally all `required-envs` for this deployment are passed into the service. These values can be overwritten using this variables.|No|

The schematic flow when running the system-test is as follows:

1. Build the system test container from `./systemTests/\<app-name\>/`.
2. Create a temporary docker network.
3. Try to remove left-over services from previous run.
4. Run all defined services in the background.
5. Wait for all services to become ready.
6. __Run the system test container in the foreground.__
7. Remove the services containers.
8. Remove the temporary docker network.

### System Tests for CronJobs

#### Introduction

If \<app-name\> is a cronjob, the sytsem-test is run in "cronjob"-mode, which spins up a temporary Kubernetes cluster using `kind`.

See [Automatic docker login](#automatic-docker-login)

`kubedev system-test`'s behaviour is defined in a "systemTest" sub-element of the cronjob definition.

#### Configuration

The following configuration options are available:

|Configuration element|Description|Mandatory|
|---------------------|-----------|---------|
|`systemTest.variables`|Defines global variables that are passed as environment variables into the services (if defined) and the system test container|No|
|`systemTest.testContainer.variables`|Defines variables  that are passed as environment variables into the system test container, but not the services|No|
|`systemTest.testContainer.buildArgs`|Defines build args that are used when building the system test container|No|
|`systemTest.testContainer.services`|Defines services that are run outside of the cluster when running the system test container. This can not reference apps from the `kubedev.json`, because the whole service is deployed to the cluster and hence all apps run, anyways.|No|
|`systemTest.testContainer.services[...].hostname`|This service will be available by this hostname from the system test container|Yes|
|`systemTest.testContainer.services[...].ports`|Defines ports that are published from this service|No|
|`systemTest.testContainer.services[...].variables`|Defines additional environment variables that are passed to this service.|No|

#### Flow

The schematic flow when running the system-test is as follows:

1. Build the system test container from `./systemTests/\<app-name\>/`.
2. Build and push all apps from `kubedev.json`.
3. Spin up a new [kind](https://kind.sigs.k8s.io/) cluster.
4. Run a [special service](https://github.com/daniel-kun/kubedev-systemtest-daemon) that can be used by the system-tests to easily start the CronJob. The API below.
5. Cluster initialization: , install `tiller` using `helm init`
- Create a `tiller` service-account with cluster-admin permissions
- Run `helm init` to install tiller
- Create the secret defined by `imagePullSecrets` with the content `.dockerconfigjson: <base64-encoded ${DOCKER_AUTH_CONFIG}`
- Wait for `tiller` to become ready
6. Deploy this service
7. Run the system-test container

#### Run the CronJob from within the system-test

A convenience service is provided for the system-tests to easily start the CronJob and fetch the logs.

Use this endpoint to trigger the endpoint:

```
POST http://${KUBEDEV_SYSTEMTEST_DAEMON_ENDPOINT}/execute

Api-Key: ${KUBEDEV_SYSTEMTEST_DAEMON_APIKEY}
```

e.g. using curl you can use:

```bash
curl -X POST -H "Api-Key: ${KUBEDEV_SYSTEMTEST_DAEMON_APIKEY}" ${KUBEDEV_SYSTEMTEST_DAEMON_ENDPOINT}
```

The service will send individual lines, first consisting of the commands that it executes, and then with the log output of the CronJob.

A system test case should be designed to first set up the environment - such as the database or whathever is required by the CronJob, then run the CronJob using this convenience service and afterwards either inspect the logs or check the environment for expected changes - such as a new or updated entry in the database.
