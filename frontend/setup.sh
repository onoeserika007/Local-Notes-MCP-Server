#!/bin/bash
# 前端安装和启动脚本

cd "$(dirname "$0")"

echo "正在安装依赖..."
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# 使用淘宝镜像加速
npm install --registry=https://registry.npmmirror.com

if [ $? -eq 0 ]; then
    echo "依赖安装成功！"
    echo "启动开发服务器..."
    npm run dev
else
    echo "依赖安装失败，尝试重新安装..."
    rm -rf node_modules package-lock.json
    npm install
fi
