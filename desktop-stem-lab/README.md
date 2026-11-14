# NIGHTMIX 本机分轨工作站

双击 `启动本机分轨.command`，浏览器打开 http://127.0.0.1:8765 。关闭终端即停止服务。

- 搜歌：通过 yt-dlp 的 YouTube 搜索列出5个候选，确认歌手/版本后下载MP3。
- 链接：支持 yt-dlp 可解析的平台，受网络、登录、平台规则、地区限制；无全网/DRM绕过保证。不读取浏览器Cookie。仅下载有权获取的内容。
- 本地音频：MP3/M4A/WAV/FLAC，500MB以内、30分钟以内；FFmpeg识别实际内容。
- 点击“开始分轨”，Mac CPU运行Demucs htdemucs，完成后试听、下载4个24bit WAV或ZIP。
- AirDrop ZIP至iPad，“文件”中解压，DJ台分轨窗口分别导入 vocals.wav、drums.wav、bass.wav、other.wav。
- 所有任务/模型/音频在 `local-stems/data/`；不上传云服务器、不使用GPT Token；首次模型下载需联网。完成后可离线处理本地音频。分离质量随歌曲而异。
- 网页只监听本机127.0.0.1，不对局域网或公网开放。电脑需保持唤醒。

安装：需Python3.13和FFmpeg，运行 `python3 -m venv .venv` 后 `.venv/bin/python -m pip install -r local-stems/requirements.txt`。
模型/实现： https://github.com/facebookresearch/demucs （MIT）；下载器： https://github.com/yt-dlp/yt-dlp （Unlicense等，见项目说明）。
MP3为音源转码，不能提升原始音质。当前采用CPU，尚未实现Apple GPU加速。
