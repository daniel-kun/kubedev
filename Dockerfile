FROM python:3.6
WORKDIR /package/
RUN pip install pipenv
COPY Pipfile ./
COPY Pipfile.lock ./
RUN pipenv install
COPY kubedev ./kubedev
COPY ./kubedev/templates ./kubedev/templates
COPY MANIFEST.in ./
COPY tests ./tests
COPY test_utils ./test_utils
COPY setup.py ./
COPY LICENSE ./
COPY README.md ./
ENV TRAVIS_JOB_ID=99
RUN pipenv run python -m unittest discover
RUN pipenv run python setup.py sdist bdist_wheel

FROM python:3.6
WORKDIR /scratch/
COPY --from=0 /package/dist/ ./dist/
RUN pip install ./dist/kubedev-0.0.99.tar.gz
COPY --from=0 /package/tests/kubedev.spec.json ./kubedev.json
ENTRYPOINT /bin/bash -c "python -m kubedev generate && find ./"
