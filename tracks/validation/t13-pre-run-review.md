# T13 独立执行前审查

2026-10-27。**只读源码及 CPU 输入字节核查；没有导入 Torch、运行模拟/AD/优化/GPU。当前无已知执行阻断。** 本文件不是执行授权或数值结果；由 root 冻结并控制唯一运行。

审查版本：

| 文件 | SHA256 |
|---|---|
| runner.py | `0c35cd801bb4930679044b9b8490336b2de05978459b0e51d83b53fb390dcdbe` |
| config.json | `ff05ce0ab91fbfb0ba91e051483615bc369343eb16d788c599eee98df14d7cc4` |
| PROTOCOL.md | `0d68a197f4e165bb61319663d1179a69b6f5ade512bb5037e2333bdb8a08d20f` |
| inputs.npz | `fc5a87b81aac9765d7fb886b7a5d74950d7bab9dd6ae475bad716c9dccb01470` |
| inputs-manifest.json | `b898774c8891691ac84cc07d8c038e9373dca15ef15c8f13d86cdcc5f1e8e4e0` |

独立 NumPy 直接打开输入包及 T12 原 reference、analytic、两份 direction NPZ，12项数组 dtype、shape、bytes 全部相同，源 NPZ/summary SHA 与 manifest 一致。包内只选固定 rho0、seed theta/v、扰动 theta、观测码/区间、风场/势、分母、方向；不继承旧梯度、乘子或优化器状态。扰动是原 analytic.theta 本身，未重复添加。

独立 AST 比较确认 `initial_velocity`、`diagnostics`、`advance`、`phr` 整函数，观测20步循环、两个future循环和约束表达式与 T12 一致。新 `observe` 仅抽取原前缀；`complete` 从候选初态重跑前缀再追加两支未来，没有用旧末状态接续。163842项 PHR SUM、原像素逐项区间与实际细网格初始速度先验保持；删去响应目标。投影仍保留参数产生的 DC，固定基流不等于固定各候选的均值速度。

`consider` 在完整forward记账、独立clone并保存候选之后、backward之前抛出 `CandidateFound`。该异常与预算/数值异常分开处理，不回滚覆盖候选、不等待optimizer接受、不按响应大小选择。可行性与 `max|v0−vseed|>1e−10` 联合判定，另报相对L2。只对首候选做一次付费60步末验，再核全部原门和非seed；失败不换候选。无候选仅保留明确标为失败诊断的最小违约点，不算未来、不fallback seed。

新G0是9次20步观测和1次reverse，原L2单位方向/h/FD门、数值门和allocator门明确。搜索/验收miss/最终验证共80调用上限；closure留两个槽，普通观测留最终槽；20与60步独立计数，最多1820实际step（含G0）。300秒搜索软限、600秒wholeworker硬限，不把单次call当与T12等成本。候选从line-search出现时origin与未返回优化器的事实被记录。

尚未验证实际执行、梯度、内存或可行性。即便通过，1e−10非同一性门也只排除数值身份，不保证实用响应差或证明T12失败的唯一原因；未找到也不证明唯一性。严格限此次普通Phase-I资格，不引出新求解机制主张。
