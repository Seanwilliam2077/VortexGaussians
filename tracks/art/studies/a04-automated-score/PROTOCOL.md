# A04：自动编排短片草稿

冻结于 2026-10-27，首次录制前。它是 agent 编排的自动演示草稿，不是作者排练、观众反馈或艺术效果证据。原页面、demo、合成 PLY 与原求解/显示参数均不改，不填表单、不保存创作笔记。

唯一流程：打开原页面并保留加载过程 → 载入合成示例 → 第二阶段默认位置点火一次 → 点击“推进 1 秒”一次并等其自行停止 → 第三阶段重置一次 → 展示回执 → 收起一次 → 展开一次。滚动仅用于展示已有画面/按钮。没有播放10秒、调参数、额外点火或模拟；模拟时间与墙钟时间分别记录，不能将录制帧率称为实时模拟。

只允许一次录制尝试。使用已安装的 Playwright 与显式 Edge executable，headless、独立非持久 browser context、1280×800 viewport/recordVideo size；单独 loopback 随机端口，不能连接用户8137服务、现有浏览器或原localStorage。通过普通locator点击/滚动及可见DOM读数操作，不 evaluate demo/API/私有状态。显式 `--execute` 才创建浏览器。默认 out=`run-01` 且拒绝覆盖。

目标整个浏览器段≤60秒（58秒关闭看门狗）；每阶段有限等待，不剪切、加速或删除失败画面。创建 context/page 的 encoder 缺失或其它失败保留完整日志/错误，关闭本任务资源，不下载/安装、不重试。只读依赖定位中尝试旧 Playwright registry 文件路径失败属于元数据查询错误，未创建浏览器或录制；实际录制只计算本工具的唯一执行。

录制前后认证 art.html/js/css、demo、PLY、runtime、本工具/协议 SHA。保存可见状态、实际动作墙钟、截图、错误及视频路径/大小；可读时从原视频容器/既有解码工具检查时长与关键帧，不重编码视频。≤20MiB 的原WebM可由主代理纳入Git；更大文件仅本地保留并在本目录忽略，不上传媒体。本任务不自行提交代码。

成功不等于艺术研究通过：对开头、燃烧、重置和回执的可读性只做单列 agent 评议。若无法录制，则只报告失败阶段和未发生的动作，不能用旧截图假冒这次影片。

复现（仓库根，环境变量只用于本子进程）：

```powershell
$env:PLAYWRIGHT_MODULE='<existing absolute playwright package directory>'
$env:BROWSER_EXECUTABLE='<existing absolute msedge.exe>'
& '<existing node.exe>' tracks/art/studies/a04-automated-score/record.mjs --execute
```

不传 `--execute` 仅打印计划，不启动页面。脚本不会安装任何依赖。
