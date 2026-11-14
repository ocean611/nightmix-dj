# NIGHTMIX DJ Studio — Cloudflare版

安装Node.js，运行 `npx wrangler login` 与 `npx wrangler pages deploy public --project-name nightmix-dj-studio --branch main`。

浏览器播放、混音、录音、速度音调；分轨使用Mac本机工具并AirDrop四轨WAV到iPad。Cloudflare版无服务器分轨API，不上传音乐。不携带原服务器IP、访问码或私人文件。SoundTouchJS许可证在public/soundtouch/LICENSE。iPad仍需真机验收。

## v1.0.3
滑块在拖动过程中实时更新音频，已启动音频引擎的控制不再等待resume；保留短平滑抑制爆音。热Cue：点清除，再点要删除的Cue。
分轨与速度音调滑块已上移并增加底部安全留白；青/紫舞台配色。四轨文件总上限2GiB，另有解码后内存预算（桌面768MiB、iPad/iPhone384MiB，含另一碟）；文件大小上限不代表所有2GiB音源都能装入内存。
音效保留DOWN/IMPACT，新增Drop Hit/Sub Drop/Crash/Reverse Crash，独立实时音量。新增素材使用原作者CC0录音，来源和处理说明位于public/samples；不是任何热门商业曲的原版样本。

## v1.0.4
解决iPad第二碟因旧内存预算受阻：支持共享内存的隔离页面里，波形与AudioWorklet共享同一份Float32 PCM，不再为音频线程复制整套四轨。不降采样、不改变立体声。共享模式PCM总预算iPad1GiB/桌面2GiB；非共享模式iPad512MiB/桌面1GiB，按两碟合计。文件合计仍限2GiB；预算不是任意2GiB音源都能载入的保证。
界面加强青/紫/粉渐变，按钮按下光晕与扩散灯效，支持独立多指与键盘反馈，遵从减少动态效果偏好。

### 最终界面与参考音效
移除圆角分组卡片，改为开放硬件台面、切角控制键与细分隔线；Orbitron字体按OFL自托管于public/fonts。渐变光场持续旋转流动，按钮按下有独立扩散灯效；舞台灯效可切换节奏/流动/关闭。播放时跟随交叉推子主导的唱盘，空闲时自循环；间歇低亮度彩色脉冲最多每秒2次，系统减少动态偏好下不播放连续灯光。
采样栏仅DOWN、IMPACT和用户给定抖音参考视频中选取的SCRATCH 01、SCRATCH 02、VINYL STOP；原先的4个新增CC0转场音已从当前包移除。视频作者不渴鲤鱼；仅短片段，来源与时间点在public/samples/SOURCES.json，不将它们宣称为CC0。
