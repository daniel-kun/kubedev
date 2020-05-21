import os

import setuptools

with open("README.md", "r") as fh:
  long_description = fh.read()

setuptools.setup(
    name="kubedev",
    version=f"0.0.{os.getenv('TRAVIS_JOB_ID')}",
    author="Daniel Albuschat",
    author_email="d.albuschat@gmail.com",
    description="Kubernetes development workflow made easy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/daniel-kun/kubedev",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
