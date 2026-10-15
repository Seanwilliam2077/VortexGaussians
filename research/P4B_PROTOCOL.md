# P4b：有限热容交换接入实际三维 VPM 的协议

日期：2026-10-15。方法、矩阵与判定在正式运行前冻结；尚未启动正式矩阵。最终 case 定义、源码指纹与输出 schema 一同记录。P4a 已独立归档。

## 1. 本轮问题与结论边界

本轮检验标准的显式有限容量气固热交换，是否正确接入现有 native 三维 VPM：气体与固定 surface 节点交换热量，更新后的气体温度改变浮力/斜压/运动，而运动又改变下一步交换几何。采用固定 parcel 集合，无燃烧、燃料、氧气、气体生成、冷却、密度衰减或粒子退役。

本轮没有候选新方法，也没有 native surface 对独立物理 proxy 的竞争。显式 surface 节点本身就是当前独立材料 proxy。接口通过只能建立后续研究的可信基线，不能据此声称新颖性、SIGGRAPH 就绪、真实火焰精度或运行速度优势。

必须分开报告：

1. **等价与实现正确性**：热交换借贷、稳定 ID、Float32 映射、native 声明积分公式、开关隔离及观察操作无干扰。
2. **因果暴露**：反馈确实改变位置；运动确实改变热交换结果。阈值仅排除没有暴露到机制的测试，不是物理精度标准。
3. **时间细化诊断**：同一离散模型在较小 outer step 下如何变化；最细步长不是物理真值，没有预设严格单调通过要求。

## 2. 状态、测度与时间层

唯一热能状态为 Float64 Kelvin 数组；容量固定，`C_surface = area * arealCapacity`，`C_gas = volume * volumetricCapacity`。显热为 `E = sum(C_i * T_i)`。native 浮力直接加入速度，涡量有阻尼及限幅；本轮不建立机械能对等账，因而**不声称显热加动能总守恒**。

热图沿用 P4a：

`G_sg = beta * A_s * V_g * 3 / (pi*h^3) * max(0, 1-r_sg/h)`。

每个热子步读取同一旧温度，以同一个 `Q = G_sg*(T_g-T_s)*substepDt` 对 surface 加、gas 减。CFL 子步数沿用 P4a：`max(1, ceil(dt * max_i(sumG_i/C_i) / safety))`。没有温度裁剪、源或损失。

每个 outer step 固定以下一阶分裂次序：

1. 在真实积分前位置 `x^n` 上按持久 ID 重建热图。只采用新 graph，保留旧 Kelvin state、time、steps 与 cumulative；不能采用 builder 返回的初始 state 覆盖历史。
2. 热子步期间冻结图，交换得到 `T^(n+1)`。
3. feedback 开启时，动力温度为 `(T_g^(n+1)-300)/300`；关闭时固定读取每个 gas ID 的初始 Kelvin 映射。交换开关与反馈开关独立。
4. 将映射写到 native `Tb`，由原有打包路径舍入为 Float32；在 `x^n` 上建立 native 三维树，执行一次原生场计算、涡量更新与位置积分。
5. 记录 `x^(n+1)`、Kelvin、field、账本及域检查。下一 outer step 才用新位置重建图。

时间层为 graph/field geometry `t_n`，thermal interval `[t_n,t_n+dt]`，field-driving Kelvin time `t_n+dt`，native forcing clock `t_n+dt`。这是显式一阶分裂，不称同时隐式耦合。

native `TT` 是原有 self-aware 温度滤波，不是第二份热容。Kelvin → 动力映射 → Float32 舍入只能单向传递；禁止将 `TT` 或 Float32 温度写回 Kelvin。`displayT` 与固定 `density=1` 只作显示/原模型状态，不进入容量。固定 `displayT=clamp((T_K-300)/300,0,1.6)`；该显示量不得反馈动力。

native `G` 仍是原 solver 的涡量约定；其 `C3` 由 `gam*VPM_KGAIN*HX*HY*(sliceDepth/max(2,layers))/(4*pi)` 决定，不由作者输入的气体体积推导。本轮不检验或声称 gas 拆分后的流体不变性。

## 3. 预定输入和参数

主工况气体为 64 个点：`x,z ∈ [-.12,-.04,.04,.12] m`，`y ∈ [.40,.48,.56,.64] m`。每点 `volume=.08^3 m^3`，`volumetricCapacity=3 J/(m^3 K)`。初始 `T_g=560+40*(x/.12)+20*(z/.12) K`，范围 500–620 K；`G=(.15*z/.12,.25,.15*x/.12)`，`sg=.07`。

surface 为左右两个固定平面 `x=±.20 m`，各 16 点，y/z 与气体中心一致；每点 `area=.08^2 m^2`、`arealCapacity=2 J/(m^2 K)`。左面 330 K，右面 390 K。这些是明确的合成模型参数，不是木材测量值。

所有主工况固定：`h=.30, beta=4, safety=.9, maxSubsteps=100000`；映射 `ambientK=300, scaleK=300`。native 参数 `gam=1, theta=.6, baro=1.4, stretch3=1, buoy=.5, turb=0, wind=0, layers=3, sliceDepth=1.2`；`source.vx=0`，`eps=.07`，VPM grid constants 来自锁定的 `NX=32, NY=48`。完整实际参数与导出 native constants 必须保存，不只保存上述摘要。

主工况 1 s，基准 dt=1/60；细化 dt=1/120、1/240。出生、旧源带加热、旧热/视觉冷却、密度衰减和实际删粒全部绕过。初始化后 RNG draws 应为零。Kelvin 必须保持原初值范围，主工况位置必须保持 native transport 与 Morton 域内。

单步解析工况：一个 surface `[-.20,.4,0]` 和一个 gas `[-.12,.4,0]`，沿用主工况 area/volume/capacity，`T_s=330 K,T_g=560 K`，`G=0,sg=.07,baro=0`；其余 native 参数不变，dt=1/60，只运行一步。独立代数复算采用实际离散热子步，然后检查 Float32 映射、单点 self-aware TT、浮力及 Euler 位置；不是将显式 Euler 终点误称连续热 ODE 的精确解。

## 4. 完整 12 例矩阵

| ID | 设置与用途 |
| --- | --- |
| `single-step-analytic` | 上述单点一步接线检查。 |
| `main-no-exchange-no-feedback` | 主工况 exchange=false / feedback=false，动力控制。 |
| `main-no-exchange-feedback` | exchange=false / feedback=true；动力逐步等于前一控制。 |
| `main-exchange-no-feedback` | exchange=true / feedback=false；Kelvin 交换，动力仍逐步等于控制。 |
| `main-coupled-dt60` | exchange=true / feedback=true，主耦合结果。 |
| `main-static-exchange` | 相同热初值、固定气体位置，作为移动几何的热对照。仅比较热态，不要求其 life/动力 hash 等于移动 arm。 |
| `main-coupled-dt120` | 主耦合，dt=1/120。 |
| `main-coupled-dt240` | 主耦合，dt=1/240。 |
| `uniform-exchange` | 全部节点 450 K，exchange=true / feedback=true。 |
| `uniform-no-exchange` | 全部节点 450 K，exchange=false / feedback=true。 |
| `main-coupled-observed` | 与主耦合相同，每步 camera(yaw=.7*sin(frame*.17)) 及额外两次 snapshot；观察前后全状态不变，回放与主 arm 相同。 |
| `main-coupled-reordered` | 主耦合输入 surface/gas 数组分别全 reverse；canonical String(ID) 排序后回放完全相同。 |

运行前验证稳定 ID 唯一、所有输入有限且容量/测度/sg 正、映射域合法、主几何初始严格域内。不根据完整运行结果替换参数、初态、时间顺序或暴露阈值。quick 仅检查接线和 schema，不代替完整 12 例证据。

## 5. 原始证据与独立复算

每个 outer step 保存全部 canonical IDs、气体积分前后位置/速度/G/sg/life/density、真实 Float64 动力 Tb 与实际 Float32 packed inputs、native raw/packed field outputs、Kelvin/capacity、完整热 graph 与 ledger/cumulative、cloud Morton order、参数及计数。surface、gas 的热节点顺序与 cloud 数组顺序不能混用。

独立审计从保存的几何/measure 重建热系数和子步，复算同一 Q 借贷、容量、Kelvin、实际 `sum(C*T)`。不能只验证 `netSurface+netGas` 自消，因为那不足以证明实际温度更新守恒。

动力审计利用保存的实际 native field 复算声明的 baroclinic 增量、stretching、阻尼、G 限幅、温度浮力、速度限幅与 Euler 积分；保留 Float32 存储顺序。这是**条件于实际场输出的积分检查**，不声称已独立验证 Barnes–Hut 树、Gaussian kernel 或温度梯度的物理精度。单点解析例另给一个不依赖多点树近似的接线检查。

动力比较应包含实际 driving Tb、packed/field、位置/速度/G/sg/life、source/RNG/时钟与 native 常量，但排除纯 displayT、Kelvin、相机、计时及 exchange/feedback 标签。完整状态另存 Kelvin/display/config/计数；不能因为跨控制 arm 的配置与热态本来不同而要求 fullStateHash 相同。camera/reorder 等同 arm 等价同时检查字段与 hash，不能仅靠短 hash 宣称状态相等。

## 6. 判定合同

实现正确性：

- 显热与热账本相对误差 <=1e-12；能量标度固定为 `max(1 J, abs(E0))`，与 P4a 一致。独立离散热子步 Kelvin max error <=1e-9 K。
- 无出生、删粒、native 加热/冷却、密度衰减、初始化后 RNG 消耗或 ID 丢失；同时检查实际状态，不只依赖计数为零。
- 任一 Morton 出域、transport boundary 出域、实际 z 夹持或 native would-retire 触发，则该运行 invalid。梯度/G/speed 限幅属于声明的原生模型，逐项记录并独立复算；其发生本身不删 case、不事后宣称模型因此无效。
- 主无交换两 arm、交换但无反馈 vs 控制、等温交换开关的动力回放逐步精确一致。等温热通量为零。observer/reorder 与主耦合的相应完整数值回放精确一致。
- 独立 native 积分复算采用 absolute tolerance 1e-12、relative tolerance 2e-13（`abs(actual-reference) <= 1e-12 + 2e-13*abs(reference)`）；实际 raw → Float32 存储字段要求 exact。保存每个预定 outer step，缺失记录不能标为通过。

因果暴露（独立于正确性）：

- `main-coupled-dt60` vs `main-exchange-no-feedback`：最终全部 64 个稳定 gas ID 的三维位置 RMS 差 **>1e-6 m**。
- `main-exchange-no-feedback` vs `main-static-exchange`：最终全部 96 个同 ID 热节点的容量加权温度 RMSE，`sqrt(sum(C_i*deltaT_i^2)/sum(C_i))`，**>1e-6 K**。
- 差异未达阈值称机制未充分暴露，不称“证明没有反馈”。最大误差、各分量差异及热交换量可描述性报告，不能替换预定 RMS 指标。

时间细化：比较 dt60/dt120 对 dt240 的最终 stable-ID 三维位置 RMS 及全部热节点容量加权温度 RMSE，并报告实际热子步计数。可保存共同物理时间的误差曲线辅助解释。没有硬性单调 gate、没有物理精度通过线；若不改善，完整报告并诊断，不能自动把最细结果当真值或改变分裂顺序追阳性。

三类结论分别记录：execution/integrity、equivalence/correctness、causal exposure；时间细化作为诊断。未全部完成不能标完整协议。任何失败不省略余下可安全执行的预定 case；非法数值/域问题须显式保留失败状态。

## 7. 本轮结束后仍缺什么

即使全部正确并暴露双向作用，也只验证这个固定 parcel、短时合成工况的接口。它没有燃烧源项/质量账、真实材料标定、气体生命周期、障碍物条件、空间收敛的物理解、任意采样一致的 VPM、图像质量或成本证据。后续必须让一个具体候选在同物理输入、相同求解器和渲染器下挑战独立 surface proxy；当前 standard proxy 的正确性不能充当候选方法的新颖贡献。

本协议只冻结上述试验，不承诺任何结果。运行命令与实际 schema 见同目录 `P4B_README.md` 及 `p4b-design.mjs`；正式输出必须附运行前后 source 指纹。不得根据结果更改物理参数、矩阵、暴露指标或误差容限。
