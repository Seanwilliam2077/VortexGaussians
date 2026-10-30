# TOG 研究轨道：从创作需求到可审查任务

**当前进度（2026-10-30）：** [T67](tasks/t67-compact-mixture-contract/README.md) 已完成普通正双高斯的解析合同与独立复核：固定几何时，幅值可解析消去，混合权重受四次多项式约束，至多有一个非退化驻点。这尚未给出双高斯的数值容量结果。下一轮按已固定协议检验八参数普通模型是否足够：最多 2233 次几何提案、单次 120 秒/观测峰值 512 MiB，并用原单高斯作校准、固定候选在 S128 上直接复核。本轮没有数组读取、数值求根或科学运行；T56/T57/T58/T59/T60/T63/T65/T66 系列累计科学时间仍为 1980.2512354997452 秒，不代表项目总计算量。历史失败保留，TOG 核心贡献未建立，目标 active。

**目标是形成可发表的研究贡献；目前没有已经建立的 TOG 贡献。** 此目录首先把“艺术 brief—物理控制—像素指标”变成明确、可携带的输入合同。它提供普通共同模型、规格检查和单次控制验收，不包含响应缓存、新优化算法或自动创作系统。原仓库 demo 和既有 research 保持原状。

首个 [artist brief](configs/artist-brief-001.json) 是“改变左上运动，保留右侧批准画面”。这是研究人员提出的需求草案，尚不是经过创作者验证的真实需求。下一步是取得或编写具有来源记录的独立目标图，审视它是否表达所需动作，再检验用户给出的控制。这里允许直接 authored 目标，不要求从一个已知可行见证倒推出目标，也不保证任意目标在本模型中可达。

## 映射合同

| 层 | 当前可操作定义 | 尚未证明的内容 |
|---|---|---|
| 创作意图 | 左烟上部朝画面中央弯曲，右侧批准画面保持 | 需求的外部价值、动作的艺术可读性 |
| 输入目标 | 25 帧编辑 ROI 的 alpha 数组，独立来源与 SHA256；允许 authored/observation/synthetic_witness，必须明示 | 图像可达性、观测的动力学真实性 |
| 物理控制 | `(4,3,8,8,8)` MAC 体力系数 q，共 6144 个变量，时间结点为更新 0/13/26/39 | “弯曲”没有唯一力场逆映射；接口不替用户求解 |
| 画面指标 | 每帧保护相对 RMS≤2% 且绝对 RMS≤.005；编辑≤5% 且≤.01；参考信号≥.01 | 指标通过不代表艺术意图通过 |
| 运动描述 | 左上/左下 alpha 横质心变化、alpha 总量比 | alpha 质心不是物质轨迹；新 brief 不借用或放松历史 2px 门 |

ROI 为 `[x0,y0,x1,y1]`，左下原点、右上不包含；NumPy 数组仍为 `[frame,y,x]`，行随相机向上增大。两个保护 ROI 是 `[35,13,53,33]`、`[35,33,53,55]`；编辑 ROI 为 `[10,12,34,55]`，包含上部和下部上下文。帧编号是完成物理更新后的 16..40，而非零起始更新号。

共同模型是周期 32³ MAC 不可压被动烟，40×.025 时间步；无燃烧、浮力、源项、障碍或真实物性主张。旧速度半拉格朗日推进后加力并做完整 FFT 投影；密度非负但不严格守恒。主相机绕 y 轴 20°，实际光学采样为 32²×64，再把 alpha 插值到 64²；输出分辨率不代表 64² 独立射线。`src/core.py` 与 R20 **逐字节相同**；`src/scene.py` 是明确的 fork，原 `initial_state` AST 不变，只移除了见证/目标配方。来源见 [provenance.json](provenance.json)。

## 命令（仓库根目录）

Python 3.10+；纯规格/计划检查只需标准库。离线图片复核需 NumPy。模拟另需 Torch；原环境为 Torch 2.11、float64。依赖清单是 [requirements.txt](requirements.txt)，本入口不自动安装、修改系统环境或选择 GPU。

```sh
# 默认只验规格与来源，不导入 NumPy/Torch，不模拟
python tracks/tog/research.py
python tracks/tog/research.py approve --out tracks/tog/runs/approved-01

# 显式生成零控制批准图（CPU 默认；添加 --device cuda 才选 GPU）
python tracks/tog/research.py approve --out tracks/tog/runs/approved-01 --execute

# authored 目标已在独立 brief 中附好后，先只检查/计划
python tracks/tog/research.py validate --brief tracks/tog/configs/my-brief.json --require-target
python tracks/tog/research.py evaluate --brief tracks/tog/configs/my-brief.json --controls my-q.npy --approved tracks/tog/runs/approved-01/approved.npz --out tracks/tog/runs/control-01

# 明确执行一次；没有拟合/优化/扫参
python tracks/tog/research.py evaluate --brief tracks/tog/configs/my-brief.json --controls my-q.npy --approved tracks/tog/runs/approved-01/approved.npz --out tracks/tog/runs/control-01 --execute

# 离线核验已保存 R22 失败图像，不运行模型
python tracks/tog/research.py history --execute
python tracks/tog/check_interfaces.py
```

`--out` 必须不存在。模拟在子进程执行，规格中的 `wall_seconds` 是包含导入、初始化、一次 rollout、读回和 IO 的整 worker 上限；超时保留日志。`max_rollouts=1`，不进行优化。CUDA OOM/运行失败保留为失败，不会回退到另一配置。输出 `synchronizedRolloutSeconds` 只是该单次调用，不构成性能比较或交互帧率。

`approve` 生成 `approved.npz`（v0、rho0、25 帧、末 v/rho）、`summary.json` 和三个 PGM 预览。零控生成并不等于已经取得人的艺术批准，需要先看图。预览为 8 位、已翻为普通图片的左上原点；数值 NPZ 为 float64、保持左下原点。

## 数据接口与目标来源

复制 JSON 建立新任务，保留来源而非覆盖历史。`target.path` 必须是**相对该 JSON** 的文件路径；`sha256` 是文件 SHA256；NPY 用 `key:null`，NPZ 必须指定 member。推荐 authored 目标形状 `(25,43,24)`、`layout:"edit_roi"`；也可提供 `(25,64,64)` 的 `full_frames`，CLI 仅裁剪已声明编辑 ROI。目标帧次序严格等于 `target.frame_ids`。数组须为有限浮点 alpha∈[0,1]；不自动缩放、翻转、裁剪数值或套用色调映射。手绘 RGB 图须由作者明确转换为 alpha，不能静默当密度/物理真值。

`--controls` 接受有限浮点 `.npy` 或 `.npz` 的 `q`，形状 `(4,3,8,8,8)`，顺序 `time,component,x,y,z`。它是原控制系数，不是 tanh 前的优化参数 x。系数最大分量≤.5、RMS≤.2，实际扩展体力最大分量≤.5；越界如实报告，不裁剪。初态始终来自共同场景。批准 bundle 的 SHA、模型和初态必须匹配；输出保存 q、完整帧和末状态，供外部复核。

`development` 可用于设计迭代，但不能报告 holdout 收益。`holdout` 规格必须标记未用于调参、评估前已冻结并给出证据引用；验证器只检查声明，不证明人没有看过数据。没有目标的草案可以验证/生成批准图，不能进行完整任务评分。当前新 brief 只提供像素与控制门，`artistIntentValidated` 永远不由 CLI 置真。

## 历史负例保持原结论

[fixtures/r20](fixtures/r20) 保存原场景和协议；共同 core 与初态可在本目录生成。这里不冒称已移植原低秩研究/导数资格的全部运行。完整旧资格、结构及收益记录仍以原封存证据为准。

[fixtures/r22](fixtures/r22) 保存原协议、完整 summary、批准图和唯一见证图/控制，小于 6 MB；这些是 byte-identical 历史副本。`history --execute` 只重算其保存图像的原语义门：上区最大位移 **1.4065755548 像素 < 2**，合格帧 **0/25**，`taskQualified=false`。保护与力预算通过也不能把它改标为通过。没有生成优化 pack，没有运行两臂优化。本目录的新草案不重新解释这个失败，也不继续调整该见证以达到 2px。

## 当前下一步

[T67 的普通双高斯合同](tasks/t67-compact-mixture-contract/README.md) 已完成；[下一有限任务 T68](tasks/t67-compact-mixture-contract/DECISION.md) 实现并静态复核该协议，冻结代码与输入后只运行一次固定预算实验。保持原始场、轴向质心、协方差门槛；严格区分根隔离/候选构造完成与连续最优性。若普通双高斯通过，就结束本端点的表示容量升级；有限搜索未找到见证仍是不确定，不自动加第三颗高斯或扩大搜索。
