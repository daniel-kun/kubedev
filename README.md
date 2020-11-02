# kubedev

DevOps command line tool that standardizes workflows for Microservices in Kubernetes for teams:

> Develop, Build, Secure, Deploy.

It builds on well-known and field-proven tools:

- [docker](https://docker.com/)
- [tilt](https://tilt.dev/)
- [helm](https://helm.sh/)
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

`kubedev` is in early development and used internally by Gira.

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
                "host_path": "/container/path" # Mount local directories to container directories when running via `kubedev run`
              }
            },
            "required-envs": {
                "MYDEPLOY_FLASK_ENV": {
                    "documentation": "..."
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
    "daemonsets": {
       # … not implemented, yet
    },
    "cronjobs": {
       # … not implemented, yet
    }
}
```

## Naming conventions

`kubedev` will work with artifacts that follow certain naming conventions that are built from the \<service name\> (top level "name"), the \<app name\> (the "name" inside of "deployments", "daemonsets" and "cronjobs") and a tag, which will be used as the image tag.

|Artifact|Naming Convention|
|--------|-----------------|
|helm chart name|The helm chart is generated with the name `<service name>`.|
|helm release name|The release name is either directly specified using `helmReleaseName` in `kubedev.json`, or is the same as the helm chart name if `helmReleaseName` is not specified.|
|kubernetes labels|All kubernetes definitions include the labels `kubedev-deployment` (\<service name\>) and `kubedev-app` \<app name\>.|
|image name|The image name is built using `<imageRegistry>/<service name>-<app name>`, except when \<app name> is the same as \<service name\>, in which case it is collapsed to just `<imageRegistry>/<app name>`|
|image tag|The tag is either built using `"${CI_COMMIT_SHORT_SHA}_${CI_COMMIT_REF_NAME}"`, if both these environment variables are set, or to `none` otherwise.|

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

When "pipenv" is included in the "usedFrameworks" by either a deployment or globally, the following files are generated inside the \<app\>'s sub-directory:

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

This commands writes the content of `${DOCKER_AUTH_CONFIG}` to the file `${HOME}/.docker/config.json`, if:
- `~/.docker/config.json` does not exist.
- The environment variable `${HOME}` is set.
- The environment variable `${CI}` is set.
- The environment variable `${DOCKER_AUTH_CONFIG}` is set.

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

Reads a kube config from the env var $KUBEDEV_KUBECONFIG (required) and optionally a context from $KUBEDEV_KUBECONTEXT and then runs `helm upgrade --install` with appropriate arguments and all env vars from `kubedev.json`.

See [Naming Conventions](#naming-conventions).

The generated image tag is passed to the template using the environment variable KUBEDEV_TAG.

`kubedev deploy` is used inside the CI/CD build jobs generated by `kubedev generate`.

## kubedev template

Basically runs `helm template` with appropriate arguments and env vars from `kubedev.json`.

See [Naming Conventions](#naming-conventions).

The generated image tag is passed to the template using the environment variable KUBEDEV_TAG.

`kubedev template` is used inside the Tiltfile generated by `kubedev generate`.

## kubedev system-test \<app name\>

Runs a system-test container against defined services, which can either be services defined in `kubedev.json`, or services pulled from a registry such as a database or a service defined in another repository.

`kubedev system-test`'s behaviour is defined in a "systemTest" sub-element of the app definition. See the thorough example at the beginning of the README.md.

The following configuration options are available:

|Configuration element|Description|Mandatory|
|---------------------|-----------|---------|
|`systemTest.variables`|Defines global variables that are passed as environment variables into the services (if defined) and the system test container|No|
|`systemTest.testContainer.variables`|Defines variables  that are passed as environment variables into the system test container, but not the services|No|
|`systemTest.testContainer.buildArgs`|Defines build args that are used when building the system test container|No|
|`systemTest.testContainer.services`|Defines services that are run in the background when running the system test container. Use the syntax `{\<app name\>` to reference deployments that are defined in this `kubedev.json`, and the image name will be built automatically according to the same rules are `kuebdev build` would|No|
|`systemTest.testContainer.services[...].hostname`|This service will be available by this hostname from the system test container|Yes|
|`systemTest.testContainer.services[...].ports`|Defines ports that are published from this service|No|
|`systemTest.testContainer.services[...].variables`|Defines additional variables that are passed to this service. When this service references a kubedev deployment, additionally all `required-envs` for this deployment are passed into the service. These values can be overwritten using this variables.|No|

The schematic flow when running the system-test is as follows:

1. Build the system test container from `./systemTests/\<app-name\>/`.
2. Create a temporary docker network.
3. Try to remove left-over services from previous run.
4. Run all defined services in the background.
5. Wait for all services to become ready.
6. __Run the system test container in the foreground.__
7. Remove the services containers.
8. Remove the temporary docker network.
