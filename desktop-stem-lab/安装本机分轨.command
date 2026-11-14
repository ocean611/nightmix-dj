#!/bin/zsh
set -e
cd "${0:A:h}"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
trap 'echo "安装未完成，请将上面的错误信息发给维护者。"; read "?按回车关闭"' ZERR
if ! command -v brew >/dev/null; then
 echo '需要先安装 Homebrew：https://brew.sh/zh-cn/'; read "?按回车关闭"; exit 1
fi
if ! command -v python3.13 >/dev/null; then brew install python@3.13; fi
if ! command -v ffmpeg >/dev/null; then brew install ffmpeg; fi
python3.13 -m venv .venv
.venv/bin/python -m pip install --cert /etc/ssl/cert.pem -r local-stems/requirements.lock.txt
echo '安装完成，正在启动本机工作台。'
exec zsh './启动本机分轨.command'
