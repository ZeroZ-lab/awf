FROM mcr.microsoft.com/devcontainers/python:3.9

# 安装 uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# 确保 uv 在 PATH 中
ENV PATH="/root/.cargo/bin:$PATH"

# 设置工作目录
WORKDIR /workspaces/awf
