FROM debian:10
WORKDIR /app/

RUN groupadd --gid 3001 app-group && \
        useradd --create-home --no-log-init --gid app-group --uid 2001 app-user
RUN mkdir -p /app && chown -R app-user:app-group /app
USER app-user

# COPY --chown=app-user:app-group SomeFile ./

ENTRYPOINT echo "Hello World"
