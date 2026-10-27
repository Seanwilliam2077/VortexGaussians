# T07 普通时序修订求解：独立源码预审

2026-10-27。**执行前 clear，无已知阻断。** 本次仅只读源码与固定输入合同，用 Python 标准库进行 AST/配置/指纹比较；没有 import Torch、执行 G0、模型 rollout、优化或 GPU 工作。T05 后审三文件保持不变。

## 审查对象与变更范围

已读 T04→T07 runner 完整差分、当前 config、PROTOCOL、static_check、T06 brief 与固定目标来源，以及共同 `WORKFLOW_COST.md`。最终候选：

| 文件 | SHA256 |
|---|---|
| runner.py | `f0932a8ee6438a06ca26346104ae7d4b33c2b7a44a38c65d9ccdc691f10f5251` |
| config.json | `7170c92e946321818fbc4806fcc305e772627af2c1da3165d802e561f3c8d800` |
| PROTOCOL.md | `b254bf66e382ac5cd369aa914423fef4a62052d49abb93431a94f88f76a539c3` |

独立 AST 比较确认 `Objective`、`acceptance`、`force_stats`、`penalty_record`、`closure`、`run_acceptance` 与 T04 完全相同。共同模型、原质量/预算门、76 约束顺序和全部求解数值配置相同；配置差异限于 task ID/目标、起点说明和成本来源记录。

目标为已冻结 T06 development 图像：onset 24、终点 40、幅度 4，空间规则、ROI 不变。目标文件 SHA `fbecf29dd9e484c17cad4a5ea9423635efc84091509d47a905612065652191b3` 与 brief 一致。它是研究人员预先编写的时序修订，不是外部用户验证、物理真值或 holdout；A4 也不是历史 R22 的质心门。

## 初始化、资格与停止逻辑

生产者从已合格 T05 final NPZ **只索引 x**，核对文件/raw-x SHA、T05 completed/source-unchanged/joint-pass 和已记录来源成本。没有读取该 NPZ 的末速度/密度、图像、乘子或优化器历史作为新求解状态。所有新 forward 仍使用共同原始 v0/rho0；lambda=0、rho=1、全新 L-BFGS 历史。首次 warm-control 验收是真正付费的完整 forward，算入 120 次预算；若已过门即停止。

新目标不复用 T05 的 G0：代码真实执行固定随机 x=.12、两方向、h=1e−5/1e−6 的 **9 forward/1 backward**；资格专用 lambda=2、rho=1，全部 76 PHR 分支须激活，原相对 FD 门为 1e−4。G0 失败即保存结果并停止，不调整步长/门。此次只确认调用链，尚未确认新目标 G0 实际通过。

原 50 保护 + 25 编辑 + 1 RMS 约束均用于 PHR、乘子和 violation 判断。mean-edit 与正则不变；验收继续使用逐帧相对 AND 绝对原门及状态/力预算。最多三轮、各 20 次返回步，AL 改变时重置历史。所有初验、closure、线搜索和返回后验收计费，预留验收槽；中途预算耗尽恢复最近接受 x 和缓存结果，不能把 trial 或历史 best 当最终接受点。600 秒外层监督包含启动、认证、新 G0、求解及 IO，结果目录不可覆盖，失败保留，无自动重试。

## 成本和证据边界

本轮新目标的资格、warm 初验与修订求解都是 T07 新成本；T05 的 84 次来源求解、60.4012885 s solve / 76.3454182 s worker 另列，不能把 T03/T04 开发探索加到新编辑在线延迟。closure 和 acceptance 同步计时嵌套于 solve，solve 又嵌套于 worker；不得相加。力/质量检查包含在 acceptance 内，证据 IO 包含于相应 wall time，未取得各自独立隔离计时。

额外 acceptance forward 沿旧审计实现保留；参数与输入身份完全相同时复用 closure 输出，是尚未实施的普通改进机会。因此本轮不是“最强可能普通实现”：慢或失败不能支持缓存必要性，不能直接形成正向方法加速结论；便宜的合格普通路径则可作为此固定两编辑序列的负向投入筛查。当前也没有候选缓存方法对照。

源代码预审不等于执行后数组审计。实际 G0、初验 x、accepted/final 数组、预算回滚、质量门及调用/成本仍须由唯一正式结果检查。最终结果只代表固定模型和这条 development 时序任务，不外推到一般创作、真实流体或 TOG 贡献。

以上是执行前源码审查；唯一 GPU 执行由 root 授权、training 代理完成。以下为 root 另行授权的独立 CPU 后审。

## 唯一运行后的保存数组复核

[`t07_audit.py`](t07_audit.py) 由既有独立 T04 数组审计窄改，未 import 生产者、core 或 Torch；使用 `allow_pickle=False`、elementwise NumPy、SHA。首次运行完成，无审计器失败或重试。[`t07-audit.json`](t07-audit.json) 的 3,287 项具名检查全部通过；数量不是研究证据强度或贡献指标。

读取并认证 45 个 NPZ（11 个新 G0 文件、33 个接受状态、1 个 final），逐数组核 shape/dtype/raw SHA/finite。用 T06 固定目标和原 approved 重算每个接受状态的 25 编辑门、50 保护门、76 约束、mean-edit/正则/PHR；独立展开所有接受控制的 MAC 空间插值和 40 个时间权重，重算力预算。原质量门没有数值放宽。

**来源与初验：** 初始 x 与 T05 合格 final x 逐位相同；新初验图像与 T05 final 图像逐位相同。lambda=0、rho=1；每次从共同 v0/rho0 起算由已核源码/输入指纹支持，本审计没有再次模拟证明。T05 图像面对新 T06 目标只有 11/25 编辑帧通过，保护仍 50/50，通过重放旧控制并不已经完成新任务。

**新 G0：** 真实保存的九次 forward/一次 backward 输出齐全。独立从 q/frames 重建 loss，再与保存的 analytic gradient 点积比较，最大相对 FD 误差 `1.4349841961040164e-6`，通过原 `1e-4` 门。与生产者标量记录末位的差异来自独立归约；这里不是新 AD 实现，也不是复用 T05 的旧目标资格。

| 原门或成本 | 独立复核结果 |
|---|---:|
| 首次全部通过 | 返回步 32 / solve rollout 101；此前无全部通过的接受点 |
| 编辑 | 25/25；最坏相对 RMS 4.99483908%，frame 37 |
| 保护 | 50/50；最坏相对 RMS 1.93676747%，上方右侧 ROI / frame 40 |
| 系数最大绝对分量 / RMS | 0.4576213944 / 0.0443758942 |
| 实际扩展力最大分量 / RMS | 0.4462726859 / 0.0332222648 |
| 新 G0 | 9 forward / 1 backward；4.3910674 s（含资格证据 IO） |
| 新 solve | 101 = 68 closure + 33 acceptance；32 返回步 |
| closure / acceptance 同步小计 | 55.0382148 s / 13.6882579 s |
| solve wall / worker wall / supervisor wall | 71.1901340 s / 91.5084740 s / 92.4505022 s |

final 的 x/q/frames/constraints 与最后接受点逐位相同，q-history 与全部接受状态一致，最终速度/密度 finite 且密度非负。未发生 budget rollback；没有选择更早状态或把 trial 升格。源/输入首尾与 freeze 一致、实际 UUID 匹配。第 20 返回步后一次 AL 更新：最大正 violation 从 5.3347862 降至 0.1194209，rho 保持 1，5 个乘子为正；随后使用新历史。正式 closure 保护有效分支最多 19，保护罚项真实参与求解。

当前 T07 新工作为 **110 次 forward（9 G0 + 101 solve）**。T05 的 84 次 source solve 和 76.3454182 s source worker 另列；若描述两任务依赖链，来源 solve 加本轮为 194 次，两个 worker 为 167.8538922 s，**不含更早的资格/探索成本**，也不能把这些合计称新编辑在线延迟。force/质量检查仍包含在 acceptance 内，IO 包含 wall；嵌套小计不相加。

这证实固定时序修订在普通 warm-parameter 路径下可满足既定像素/控制门。约一分钟求解只是一次保存的观察：尚未去除普通验收 forward 冗余，也没有新方法对照，不能由此证明保护缓存必要、收益可得或创作交互已经达标。T06 仍是 research-authored development 任务，不代表真实用户批准或广泛创作可达性。

后审限制：中间接受点未保存末速度/密度，其数值门仍依赖生产者记录；closure 没有其图像/梯度 raw，只核保存的 c/lambda/rho 算术和计费；没有独立轨迹/AD 重演或重新计时。Torch allocator 不代表完整进程/设备峰值。

审计脚本 SHA256：`acdcdaff34780f09da608537663b684d0e9c62063fb58abefe5857bebaad070e`。

审计 JSON SHA256：`5c31d124433c19e0a92eb02e08475c4584aff5c5d84c3fc70452ebfd651f43f1`。本轮后审完成并停写。
