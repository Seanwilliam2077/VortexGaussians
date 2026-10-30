# A39《末班之后》时钟维护规格

2026-10-31，首次运行前固定。全文、几何、动作、阶段、结束/重开和记录合同沿用[A38规格](../a38-after-the-last-train/WORK_SPEC.md)，仅本页列出的差异覆盖旧定义。A38数据保持。

- spreadClockMode由legacy改为原平台已有elapsed。advanceClock对全部state1推进，graph1400只限制邻居传播；frontierDeferred仍是图前沿点×步延期，不能再由它推断燃烧时钟被延迟。
- 其余参数与所有六行点构造、输入和360步上限完全相同。尤其particlePolicy仍block，粒子容量/配额没有修复，流体横向域外限制不变。
- 唯一检查对象改名为__a39，仍只公开ready/snapshot。页面方法备注和版本号更正，作品主画面、正文与动作不变。代码中的capDelayObserved仍读取图前沿延期，解释以本规格为准，不能说它代表本版clock延迟。
- 脚本另外记录最终第四/第六行的燃烧点、char/glow非零数与燃料减少；这些是维护证据，独立于艺术判断，不换算评分。

[检查协议](INSPECTION_PROTOCOL.md)复用同一预声明几何路径与释放区间。root只静态读回差异后执行一次；没有预先运行或看效果选参数。已有时钟开关不是本次的新算法、艺术发现或永久损毁机制。
