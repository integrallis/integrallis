FROM mcr.microsoft.com/devcontainers/base:ubuntu

ARG USERNAME=vscode

# Create workspace and config directories and set permissions
RUN mkdir -p /workspace /home/vscode/.claude && \
    chown -R vscode:vscode /workspace /home/vscode/.claude

WORKDIR /workspace

# Set up non-root user
USER vscode

# Set `DEVCONTAINER` environment variable
ENV DEVCONTAINER=true
