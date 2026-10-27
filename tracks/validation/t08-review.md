# T08 普通验收复用：独立窄审

2026-10-27。仅审新 T08 源码/准备记录，不改旧证据，不执行 GPU、模型或优化。最终源码、协议与当前 CPU 小测试指纹已对齐，无已知执行前阻断，可以按冻结合同执行唯一一次正式运行。本结论是源代码审查，不是运行结果或轨迹等价性认证。

## 数学与调用边界

已读 T07→T08 完整 runner 差分和 `evaluation_cache.py`。独立标准库 AST 比较确认 Objective、acceptance、force_stats、penalty_record 与 T07 完全相同；模型、T06 目标、T05 起点输入、76 约束/原门及数值配置不变。固定输入读取仍只用共同 v0/rho0、批准图、T06 目标与 T05 final 的 x，不从 T07 优化结果初始化。

T07 G0 复用在 import Torch/首次 GPU 之前执行：认证来源/输入/配置、AST、原资格标量、紧凑 q/c/gradient/direction 数组 raw SHA，再以 elementwise NumPy 重组 PHR 和 FD 原门。原资格图像未重读、AD 未重算；不得称新的资格实验。运行环境再次匹配，T07 的九次资格 forward 与本轮成本分开。

## 缓存、预算与最终验证

- 仅保留最近一次成功 closure 的 x 和 frames/velocity/density，全部 `detach().clone()`；没有存 loss、gradient 或 autograd 图。验收用当前 lambda/rho 重新计算原 PHR/质量/扩展力，AL/history 改变与 rollback 均清缓存。
- x 使用 dtype/shape/device 匹配后的 contiguous uint8 视图比较，区分 +0 与 −0。固定身份覆盖冻结合同、model/input 对象及静态 tensor mutation-version；优化中的 x/q 不参与静态身份。输入发生普通 in-place 改动或版本不一致则 miss，改动若发生在 closure 内也拒绝存储。
- 命中只免返回点的一次 forward；身份/x 不匹配即实跑。所有 hit/miss 的检查、质量/force 和 IO 都计时。没有从 trial 的低 loss 推断接受，也没有偷用更早 best。
- 初验必实跑；最多 120 次真实 forward 包含 initial、closure、miss 和 mandatory final。closure 保守预留可能 miss 与 final 两槽；预算异常恢复上一 accepted x/fields，不接受试步。此策略可能影响预算受限轨迹，不能先验声称与 T07 等价。
- 最终从 accepted x 和共同初态重新执行完整 forward，原门重算，再与接受缓存的 frames/velocity/density/constraints 按 dtype/shape/device/字节比较。两套数组分别保存，raw descriptors 包含 shape/dtype/SHA。任一不一致保留为 reuse verification failure，不能用新验证结果替换缓存并宣称成功。

CPU 小测试的必要范围是错 x、身份/输入/静态模型版本变化、clone 隔离、无 grad_fn/require_grad、rollback 清除、signed-zero miss 和预算槽。它只检验小 tensor 接线，不证明烟雾轨迹等价或性能。这里不追加矩阵；正式结果需按每个 accepted x/q/frames 的 raw SHA 与 T07 逐一对齐。

已只读核对作者保存的当前小测试记录：九项均通过，Torch 2.11.0+cu128，CUDAInitialized=false，记录中的 cacheSourceSHA256 与当前 helper 一致。审阅者未重新执行该测试；旧 pre-byte-review 记录保留。最终协议准确包含字节匹配、真实 final forward、双槽预留和资格复用限制。

## 成本解释

closure 包含缓存写入成本；acceptance 包含匹配、fallback forward（若有）及原质量/force；final verification 的真实 forward/门与比较单列。嵌套时间不重复求和。T08 不新跑 G0，而 T07 曾新跑，因此二者完整 worker wall 不能直接当实现加速比。可以核实真实 forward 调用减少和同一输入上观察到的 solve 成本；一次样本不构成统计性能结论，也不是新算法或保护响应缓存收益。普通复用成功必须与任务门通过分开记录。

旧 T07 审计不回写；T08 的跨运行等价性统一使用 shape/dtype/raw-byte SHA，避免数值 `array_equal` 对 signed zero 的边界含糊。本次先做执行前审查，尚无 T08 正式结果。

## 最终审核指纹

| 文件 | SHA256 |
|---|---|
| runner.py | 0c8c3c22b047db1a72cc0915b17320dbea66289ec19912fb97e03d7f422e8fe5 |
| config.json | 08525a44d8b4edbf590ed817ddf0834abc17e5d35ae612ccbc2428be789a839b |
| PROTOCOL.md | 98876f74fb3b367c06621797efd4b27e55a55c5608234c1a88c151b790ed0ddb |
| evaluation_cache.py | c51cacc312c8cb9a556c6951708d68b2ddc189a2c0bef4d53179e9b417bc1d1e |
| cache-contract-test.json | f7d948e02f7808e90c94a8eb7127bef410052e82d0f3ecb8dadee352d216eeb7 |

执行前审查完成并停写；无额外资格矩阵、历史重审或 GPU 操作。
