# NIGHTMIX — DJ台与Mac本机分轨工作站

- DJ台：https://nightmix-dj-studio.pages.dev/
- 本机分轨工具入口：https://nightmix-stem-lab.pages.dev/
- 安装包：本仓库 Releases / v1.0.0；Cloudflare入口也提供Mac安装包。

## 两个工具

`packages/dj-studio/` 是Cloudflare版DJ工作台：双碟、触控搓碟、EQ、波形、速度/音调、录音、四轨导入和独听。静态部署到Cloudflare Pages，不上传音乐，不携带服务器分轨访问码。电脑先分离后AirDrop四轨到iPad。

`desktop-stem-lab/` 是Mac本机分轨工具：本机Python运行Demucs，yt-dlp搜歌/下载MP3，支持M4A导入、四轨试听与ZIP下载。双击“安装本机分轨.command”，以后双击“启动本机分轨.command”。仅监听127.0.0.1:8765。首次安装和模型下载需联网，后续本地音频分离可离线。在线下载受平台和网络限制，不能保证全网、付费或DRM音乐可用。

`cloudflare/stem-lab/` 是分轨工具下载/启动入口；Cloudflare不运行本机Python程序。导出命名：歌名 - 作者 - 人声/鼓/贝斯/其他乐器.wav；元数据可编辑。

## 部署

DJ台：在packages/dj-studio下运行 `npx wrangler pages deploy public --project-name nightmix-dj-studio --branch main`。
分轨入口：在cloudflare/stem-lab下运行 `npx wrangler pages deploy public --project-name nightmix-stem-lab --branch main`。
先执行 `npx wrangler login`。部署使用你的Cloudflare账号，不在仓库保存令牌。

## 数据与验证

音乐、模型、任务、访问码、私钥与云服务器内部配置不提交。原public/和separator/保留历史云服务器版；新Cloudflare部署使用packages/dj-studio，自动分轨移到Mac处理。
已在Apple Silicon Mac上验证整首156.456秒M4A本机分离，四轨长度一致、非零且不同；搜索及MP3下载验证通过。iPad实际播放和触控仍需真机确认，分离效果与耗时因音源与电脑而异。

## 开源组件

Demucs：https://github.com/facebookresearch/demucs
下载器：https://github.com/yt-dlp/yt-dlp
SoundTouchJS音频处理器的MPL-2.0许可证随DJ包保留。FFmpeg与Python依赖由本机安装，包内不含音乐或模型权重。
