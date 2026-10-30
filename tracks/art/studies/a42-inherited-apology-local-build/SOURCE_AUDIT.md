# A42 装配前源码审计

2026-10-31。工程者委派的只读Agent art_a41_builder/a42_static_audit 检查原demo及本次合同，未修改、装配、运行或看图。下列为root按其回传整理的要点；这不是对尚未完成桥接代码的行为验证，更不是艺术评分。

- 唯一window.__demo锚点在282–4916行的IIFE内部；研究API和需要的状态已声明。桥接安装只定义接口，待iframe load后使用；不能立即访问之后才声明的EMBED。正常embed loop不推进模拟。
- researchSetScene重建几何、sceneInfo、SH、材料数组与哈希，并清零areaFeedCredit。它还设置identity参数，applyScene的slider回调可能回写sceneScale。因此必须前后核对整个P，不能只看燃料值。
- 调用路径不推进粒子、时间或RNG。应保持同一个srand函数引用及randomDraws，不调用一次随机数来“检验”下一值，也不重新seed。
- snapshot未给全外观元数据。桥接须另保留并严格比较authored的id/group/position/fuel/opacity/scale/color/areaWeight，sceneGauss的p/cov/sh/c/o，以及h/fuel/glow/char_/state。
- countersByGroup只枚举当前组；旧release计数在内部Map仍应保留。须比整个spreadRegionCounters Map和spreadCounters，不能因新快照不再枚举旧组就丢掉其成本。
- 旧frontier先检查id唯一、存在且state1，再只移除release，保留其余次序；emitCursor保留原值，不提前取模。后续现有feed自行做模运算。
- 新request全未燃、燃料1。handover前后time严格相同，阶段180步的time只近似3，不能误设浮点精确等于3。
- 当前研究路径不调用P4的相对动态import。派生页面的位置变化不能推论整个原平台所有模式都兼容；本任务只核查约定的普通VPM材料路径。

静态结论支持这一具体装配方法有可实现性，不预支逐值继承或可见继续变化。
