#!/bin/bash

# 确保 uv 在 PATH 中
export PATH="/root/.cargo/bin:$PATH"

# 创建并激活虚拟环境
uv venv
source .venv/bin/activate

# 安装依赖
uv pip install -e ".[dev]"

# 创建必要的目录
mkdir -p config/{agents,workflows}
mkdir -p app/tools
mkdir -p tests
mkdir -p logs

# 设置权限
chmod -R 755 .venv
chmod -R 755 config
chmod -R 755 app
chmod -R 755 tests
chmod -R 755 logs

# 添加环境变量到 .bashrc
echo 'export PATH="/root/.cargo/bin:$PATH"' >> ~/.bashrc
echo 'source .venv/bin/activate' >> ~/.bashrc

# 添加别名
echo "alias dev='source .venv/bin/activate && uvicorn app.main:app --reload --port 8000'" >> ~/.bashrc
echo "alias test='source .venv/bin/activate && pytest tests/'" >> ~/.bashrc
echo "alias prod='source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000'" >> ~/.bashrc
echo "alias install='source .venv/bin/activate && uv pip install -e .[dev]'" >> ~/.bashrc

# 重新加载 .bashrc
source ~/.bashrc

echo "Post-create setup completed successfully!"

