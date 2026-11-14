#!/bin/zsh
cd "${0:A:h}"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if [[ ! -x .venv/bin/python ]]; then
 echo '本机环境尚未安装，请查看README。'; read; exit 1
fi
if curl -fsS http://127.0.0.1:8765/ > /dev/null 2>&1; then
 open http://127.0.0.1:8765/; exit 0
fi
(sleep 2; open http://127.0.0.1:8765/) &
.venv/bin/python local-stems/server.py
