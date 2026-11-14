# NIGHTMIX DJ Studio — Cloudflare版

安装Node.js，运行 `npx wrangler login` 与 `npx wrangler pages deploy public --project-name nightmix-dj-studio --branch main`。

浏览器播放、混音、录音、速度音调；分轨使用Mac本机工具并AirDrop四轨WAV到iPad。Cloudflare版无服务器分轨API，不上传音乐。不携带原服务器IP、访问码或私人文件。SoundTouchJS许可证在public/soundtouch/LICENSE。iPad仍需真机验收。

## v1.0.3
滑块在拖动过程中实时更新音频，已启动音频引擎的控制不再等待resume；保留短平滑抑制爆音。热Cue：点清除，再点要删除的Cue。
分轨与速度音调滑块已上移并增加底部安全留白；青/紫舞台配色。四轨文件总上限2GiB，另有解码后内存预算（桌面768MiB、iPad/iPhone384MiB，含另一碟）；文件大小上限不代表所有2GiB音源都能装入内存。
音效保留DOWN/IMPACT，新增Drop Hit/Sub Drop/Crash/Reverse Crash，独立实时音量。新增素材使用原作者CC0录音，来源和处理说明位于public/samples；不是任何热门商业曲的原版样本。
