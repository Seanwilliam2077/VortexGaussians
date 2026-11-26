# 一笔火，怎样才算烧够？

[89 秒中文进展视频](tech-progress-zh.mp4) · [逐段旁白](narration.json) · [本轮技术论文](../paper.pdf)

| 起点 | 内容 |
| --- | --- |
| 00:00 | 同一木堆、两种点火笔画、两个机位的截止帧问题 |
| 00:12 | 共享前 24 步，在轻笔轨迹上恢复重笔状态 |
| 00:30 | 目标木材的点燃进度为什么选重笔 |
| 00:43 | 同一状态开关气体绘制，为什么主机位的画面选轻笔 |
| 01:00 | 双机位实际选笔的端到端耗时 |
| 01:12 | 独立布料模拟的进展、两位内部评审和停止状态 |

材质动画按原生逐步点火记录重建。灰色木堆由材质位置分箱后重建。气体章节的橙色是同一物理状态下开关气体绘制后，达到预注册颜色差阈值的目标投影。两种覆盖率都按同一选区的可见材质权重计量。视频采用中性重建与测量叠图，原始照片、拟合色彩和私有原生截图均未嵌入。[木堆与来源](../../../tasks/t109-common-parent-choice/figure/README.md) · [原生画面数据](../../../tasks/t127-woodpile-native-camera/README.md) · [计时与逐次调用](../../../tasks/t129-native-image-choice/README.md) · [外部布料记录](../../../tasks/t126-external-curtain-runtime/README.md)

成片为 1280 × 720、24 fps 的 H.264 视频，带普通话旁白和画面内中文字幕。用本机普通话语音生成六个 WAV 后，可用以下命令重新编码。生成脚本会验证原始画面哈希和投影权重。需要原实验输入、同一批 16 张原生截图、项目的科学 Python 环境和 FFmpeg。

```text
python narrate.py --help
python make_video.py --source FIREWOODS_INPUT --frames PRIVATE_T127_PNGS --audio NARRATION_WAV_DIR
```
