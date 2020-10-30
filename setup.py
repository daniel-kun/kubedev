import os

import setuptools

with open("README.md", "r") as fh:
  long_description = fh.read()

buildVersion = os.getenv('TRAVIS_JOB_ID')
if isinstance(buildVersion, type(None)):
  buildVersion = "99"  # Fake local dev version

setuptools.setup(
    name="kubedev",
    version=f"0.5.{buildVersion}",
    author="Daniel Albuschat",
    author_email="d.albuschat@gmail.com",
    description="Kubernetes development workflow made easy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/daniel-kun/kubedev",
    packages=['kubedev', 'kubedev.utils'],
    package_data={'kubedev': ['templates/*']},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
        'console_scripts': ['kubedev=kubedev:main'],
    },
    install_requires=[
        'pyyaml',
        'ruamel-yaml',
        'colorama'
    ]
)
