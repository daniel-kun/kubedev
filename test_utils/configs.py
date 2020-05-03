
testDeploymentConfig = {
    "name": "foo-service",
    "description": "This is a sample service generated by kubedev.",
    "imagePullSecrets": "foo-creds",
    "imageRegistry": "foo-registry",
    "required-envs": {
        "FOO_SERVICE_GLOBAL_ENV1": {
            "documentation": "Test env var #1 (global)"
        },
    },
    "deployments": {
        "foo-deploy": {
            "ports": {
                "http": {
                    "container": "8081",
                    "service": "8082",
                    "dev": "8083"
                },
                "https": {
                    "container": "8443",
                    "service": "8543",
                    "dev": "8643"
                },
            },
            "required-envs": {
                "FOO_SERVICE_DEPLOY_ENV1": {
                    "documentation": "Test env var #1"
                },
                "FOO_SERVICE_DEPLOY_ENV2": {
                    "documentation": "Test env var #2"
                }
            }
        }
    }
}
