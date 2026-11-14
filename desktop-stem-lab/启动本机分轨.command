#!/bin/zsh
cd "${0:A:h}"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if [[ ! -x .venv/bin/python ]]; then
 echo '正在安装本机环境…'; exec zsh './安装本机分轨.command'
fi
if curl -fsS http://127.0.0.1:8765/ > /dev/null 2>&1; then
 open http://127.0.0.1:8765/; exit 0
fi
(sleep 2; open http://127.0.0.1:8765/) &
.venv/bin/python local-stems/server.py
