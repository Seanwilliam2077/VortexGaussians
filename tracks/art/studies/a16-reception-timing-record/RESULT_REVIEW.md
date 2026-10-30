# A16 保存结果复核：采集结束，编码参数冲突

2026-10-30 14:05:46 UTC。结论：A16整体失败。正常采集已到ended，但唯一编码命令因参数矛盾被FFmpeg拒绝，没有MP4，也没有可供评审的秒网格图组。这是记录器兼容性缺陷，不是作品艺术失败。

本审查者参与A16预审，非盲审。此前把输出`-r 60`当成可与`-fps_mode passthrough`并用的名义声明，给出“未发现实际阻断”的判断，**漏掉了真实参数冲突**。该预审判断有误，不能用“只有运行才知道”或“原生时序不保证”淡化。保留原PREFLIGHT、脚本、合同与失败证据，不逆改历史。

## 本次核验范围

一次Python标准库只读核验了result、supervisor、全部帧索引、ffconcat、编码stdout/stderr，以及8项来源文件的实际字节摘要。结构化记录见[review.json](review.json)。没有读取、哈希或解码1552张JPEG，因此以下数量与字节合计是从索引独立重算，不能冒称逐文件可读性验证；也未重新查询操作系统进程。

索引为连续index/arrivalIndex 0–1551，共1552条，登记JPEG总字节102268103，与received/saved收据一致。索引SHA256为`9888c5e9b949ff3a964a75939d5684cf08d19709b9f20bd5efef3f2f569029c0`，与收据匹配。8项来源的before、after及本次重算均完全相同，包括冻结A14、demo与记录器。

## 正常序列与接收时轴

初态为ready、frame0、reset0/ignite0、inspect=false；只出现一对UI开始事件，开始后sequence/reset/ignite均为1。163个只读轮询没有额外reset/ignite或超过360步。ended及最终停留快照均为frame360、12模拟秒、displayDistance=5.6、handoffEqualExceptYaw=true、无错误。按既有冻结作品的阶段语义，采集流程已走完后退；本轮没有直接观看其运动。

首帧接收ns为728874464041300，末帧为728903583797400，stop为728906402034700。接收区间为31.9379934秒；首帧至点击前2.0122621秒，ended观察至stop为3.0179131秒，最后一图持有至stop为2.8182373秒，三者含义不同。

全部绝对接收ns以及含stop的偏移严格递增；重新计算的1553个微秒PTS逐项等于已存expectedPTSUS，首0、最大舍入误差500ns。ffconcat含1553个文件条目、1552段duration，逐段等于相邻已舍入绝对偏移之差，总计31937993微秒；末文件确为末图重复。尚无成片，不能把这些输入时轴检查写成输出PTS、尾包或完整解码已通过。

原CDP时间在351→352倒退约3.015041毫秒，而接收ns增加776900；该异常被原样登记、没有排序或修理，也未成为A16的停止原因。

## 失败原因与终止

[encode.stderr.log](run-01/encode.stderr.log)明确记录：

> One of -r/-fpsmax was specified together a non-CFR -vsync/-fps_mode. This is contradictory.

实际唯一encode参数同时含`-r 60`和`-fps_mode passthrough`，在打开study.mp4输出时以Invalid argument退出，耗时0.3156593秒。只有这一条媒体命令；probe、全解码及图组导出均未启动。文件检查确认study.mp4和review目录不存在，mediaValidated=false。

收据为worker exit1、无超时、still_live=false、requires_cleanup=false，context/browser/server均记为关闭；此处是保存收据的清理证据。采集区间31.9379934秒不等于总成本：浏览器阶段35.2525178秒，监督观察worker生命周期35.74122309999075秒，父终态检查35.74633279989939秒。元数据核验内部墙钟0.014735299977473915秒、CPU0.015625秒，含解释器启动命令墙钟0.7856494秒；与记录worker成本分开，未计本文撰写。

补录循环保持关闭。本轮没有浏览器、仿真、编码、改门或第三次尝试。已有艺术判断不因这项记录器缺陷改变，也不能将已完成的采集元数据冒充完整录像观看经验。
