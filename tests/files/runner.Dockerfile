# Final image
FROM gitea/act_runner:0.2.10
ENV CONFIG_FILE=/config.yaml
ENV GITEA_INSTANCE_URL=http://localhost:3000
ENV GITEA_RUNNER_NAME=actions-runner

COPY config.yaml /config.yaml
