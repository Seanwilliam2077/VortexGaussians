# A16 记录器准备

本目录从 A15 记录器作必要分支，只执行本协议的一次记录。A14 页面、demo 与 A15 的脚本、原始记录和失败结论均不修改。制作阶段只检查 JavaScript / Python 语法，不启动浏览器、仿真或 FFmpeg。正常入口为 `python execute.py --execute`；不带 `--execute` 的监督器及 Node 脚本都只打印计划。已有输出、attempt 或监督记录会拒绝运行。

`record.mjs` 使用既有 runtime、Playwright、Edge、FFmpeg / ffprobe。新 context 的正常 A14 页面 ready 后开始 CDP JPEG 采集；首个实际到达图像起等待至少 2 秒，再点击一次“开始观看”；只读轮询直到 ended（包含原有 2.2 秒后退），再等至少 3 秒并停止采集。没有暂停、手动推进、重开、参数调整或第二次点火。页面固定 SHA256 为 `3cbdaf8703bfa88c01e60d57bdf8c6b25c560cc2528fa03649ea5520cbdce6d5`，输入源前后摘要含 A16 工具、协议和本文。

每个接收事件先读取 `process.hrtime.bigint()`；纳秒以 JSON 字符串保存，并保存原 JPEG、arrivalIndex、sessionId、原 CDP metadata / timestamp 和主机 epoch。原 CDP 时间非递增只列异常，不停止、不排序、不删帧、不覆写原戳；缺失或无效时间仍失败。影片以首个 Node 接收时刻为零，以 stop 确认后立即取得的同域时刻为尾界。点击前后及只读状态保留同域纳秒；阶段出现时点只有轮询分辨率。

先用 BigInt 相减取得绝对接收偏移，再一次舍入成整数微秒，相邻已舍入值之差写入 concat duration。量化碰撞或倒序直接失败，不挪动 PTS。concat 输入 framerate 为 1000000，编码时基和 MP4 track 时基均为微秒；`-r 60` 在输入之后，仅作输出名义声明，并用 passthrough 保留 VFR。每个到达 JPEG 对应一帧，末图再出现一次标记真实 stop；不剪切、插值、加速或补齐动作。

一次编码后，同一次 ffprobe 读取帧和 packet：要求 N+1 帧、1440×1100、首 PTS 为零、PTS 严格递增，每帧相对既定微秒值误差不超过 2 微秒。保存最后呈示帧对应 packet 的 duration、帧 duration 及带符号尾差；`文件 duration − 真实 stop 偏移` 必须在 −2 微秒至 +20 毫秒之间。完整 framemd5 解码逐 PTS 对账，避免 null muxer 的 DTS 重标度问题。失败保留已得文件，不再编码修理。

唯一成片再按固定 `fps=1:start_time=0:round=near:eof_action=pass` 导出 960 宽的全部秒网格图并列出身份。此滤镜对输入 PTS 取整后丢弃或重复；videoSecond 是输出 PTS，不是精确整数墙钟截图，也不是最近源帧选取。若输出秒数超过真实 stop，`boundaryHoldBeyondCapture` 标注为边界图像延续，不算新增采集。顺序图审读不等于连续视频体验。

影片表达实际收到的图像流；接收负载、队列、传输抖动和 CDP 漏采/合并重绘可能改变节奏，不能据此声称原生全帧率、精确 compositor 呈示时间或观众体验。相邻相同 JPEG、间隔分布、超过 100 / 500 毫秒的间隔及 CDP 时间异常如实记录；静止不产帧不自动算作丢帧。末图持有至真实 stop，不能因最后 CDP 时间较早截去静止尾段。

预算保持浏览器 150 秒、含媒体处理 worker 270 秒、监督与自身树清理 300 秒；2000 JPEG 或 200 MiB 达限即失败，成片不超过 20 MiB 才可提交。Python 仅启动一个隐藏 worker，保存 attempt、退出状态、日志、部分 result 与清理情况；超时只清理自己的进程树。本次失败即停止补录循环，不安排第三次尝试。资格核验不预定艺术评分。
