# P5c — 独立标准物理核心的测试协议

版本：1；日期：2026-10-15。**root 已审定21个 case、参考公式和门槛；尚未完成 core/runner/auditor/schema 的联合冻结，尚未执行正式实验。** 小 q 级数切换点及稳定温度求值已在结果前审定，不改变 case 数与门槛。只覆盖 isolated Float64 direct-sum 核、显式强度单位、温度重建和两个受控时间 ODE。不修改 native demo，不接 MAC、renderer、热交换或燃烧。所有方法均为标准数值基础，不作新颖性或 SIGGRAPH readiness 主张。

## 1. 固定模型与数据合同

- 世界坐标单位 m，时间 s；`V>0` 单位 m³，`omega` 单位 s⁻¹，`Gamma=V*omega` 单位 m³/s。Gamma 是体涡粒子强度，不是曲线环量。
- 每源 Gaussian 宽度 `sigma>0` 为每轴标准差；温度重建本轮使用相同 source-only sigma。无 target sigma、参考网格体积、视觉 gain、LUT、树聚合或截断。变量核宽必须包含归一因子 `sigma^-3`。
- 温度 T 使用 Kelvin，`cV=3 J/(m³ K)`，容量 `C=V*cV`；只读显热 `sum(C*T)`。不得从 opacity/density/sigma 推导 V。
- ν=κ=0，无 G 阻尼、速度/梯度/G cap、风、随机力、出生、退休、固壁和位置 clamp。源数组包含自身时，使用真实 `V*W(0)`；不加先验自权重1。Γ、V、T、sigma 和坐标全部 Float64。
- 生产核心与独立审计不得共享 erf 近似、求和函数或导数代码。结果保存输入及 canonical source IDs；不得修改输入对象。允许 Kahan/稳定级数，允许 canonical 排序，但记录实现。不同输入顺序以容差检查，不冒充逐位相等。
- 所有输入须有限，V、sigma、cV 严格正；拒绝非法输入或计算溢出。空源显式无支持，不加入未声明 epsilon。Gaussian 非空源在数学上总有正支持，允许 log-sum-exp 归一及 centered-T 计算；当前实现以最大权重源的温度为中心，避免极小权重源的极大温度造成无谓消去。即使物理 D_T 在 Float64 下溢，若稳定归一权重仍有限，可返回 Tbar/gradT，并明确保存 logD_T、物理 N_T/D_T 和各自下溢标志，不能把下溢谎称没有源。本矩阵主查询不会依赖这种下溢处理。

## 2. 参考算子：符号、极限和过滤

令 `r=x-xj`、`R=|r|`、`q=R/sigma_j`，归一核

\[
W_j(r)=(2\pi\sigma_j^2)^{-3/2}\exp[-R^2/(2\sigma_j^2)],
\quad g(q)=\mathrm{erf}(q/\sqrt2)-\sqrt{2/\pi}\,q e^{-q^2/2}.
\]

`g'(q)=sqrt(2/pi)*q²*exp(-q²/2)`。定义 `F=g/R³`、`D=(q*g'-3*g)/R⁵`，

\[
u_j={F\over4\pi}(\Gamma_j\times r),\qquad
J_j a={1\over4\pi}\{F(\Gamma_j\times a)+D(\Gamma_j\times r)(r\cdot a)\}.
\]

J 的行是 velocity component，列是 coordinate derivative。`R=0` 时 u=0，`J=[Gamma]_cross*sqrt(2/pi)/(12*pi*sigma³)`。不能以设 J=0 代替极限；但 `J_self*Gamma_self=0`。小 q 应用稳定计算；审计用独立高精度 erf/级数，不复用 production approximation。

温度求积：`wj=Vj*Wj`，`D_T=sum(wj)`，`N_T=sum(wj*Tj)`，`Tbar=N_T/D_T`，

\[
\nabla\bar T={1\over D_T}\sum_j(T_j-\bar T)\nabla w_j,
\qquad \nabla w_j=-{r_j\over\sigma_j^2}w_j.
\]

这是 Shepard 场自身的商法则导数。有限域、有限点集的线性温度采样**不保证**该重建精确线性；不将 MLS/full-moment 梯度混入本合同。独立线性温度的浮力单位测试另行注入解析梯度。

竖直方向 `e_y`，`theta=(T-T0)/DeltaT`，`f=b*theta*e_y`，故

\[
\dot\Gamma_i=J_u(x_i)\Gamma_i+V_i b(-\partial_z\theta,0,\partial_x\theta).
\]

无额外 `uy += buoy*Tbar` 漂移。自由空间与周期平均模式是不同测试：本轮没有周期 Biot–Savart，也没有完整流动的独立 MAC 参考。

## 3. 不可变基础 fixture

统一中心 `c=(0,0.8,0)`。源 ID `s0` 至 `s7`，相对 c 的坐标如下，i 从0计数：

| i | px | py | pz |
| --- | ---: | ---: | ---: |
| 0 | -.12 | -.08 | -.10 |
| 1 | .11 | -.06 | -.09 |
| 2 | -.10 | .13 | -.07 |
| 3 | .14 | .09 | -.12 |
| 4 | -.13 | -.11 | .15 |
| 5 | .09 | -.10 | .11 |
| 6 | -.08 | .12 | .14 |
| 7 | .12 | .14 | .10 |

基础属性：`Vi=.001*(1+.2*i)`；`omega_i=(.5+.125*i, -.25+.05*i, .4-.03*i)`；`sigma_i=.07+.0025*i`；`Ti=300+10*i`；`Gamma_i=Vi*omega_i`。cV 按第1节。

64个固定查询 `c + .1*(a-1.5,b-1.5,d-1.5)`，`a,b,d in {0,1,2,3}`，循环顺序 a 外、b 中、d 内，ID `q-a-b-d`。任何同位拆分都保持 sigma、omega、T 和坐标，分摊 V 与 Gamma；每子源以 `parentId/copyIndex` 唯一命名并保留 anchorId。不得把同位拆分称为真实空间加密。

## 4. 六家族、21个预定 case

### A. 测度、强度与表示 — 7 cases

`measure-base`、`measure-split2`、`measure-split4`、`measure-selective2`（只拆奇数 i 为2份）、`measure-reverse`（完整倒序）、`measure-volume-half`、`measure-volume-double`。

前5条使用同一物理场；后2条保持每个 omega、sigma、T 和位置不变，把全部 V 改为 .5倍/2倍，并重新计算 Gamma。比较全部64点的 u、完整 J、Tbar、gradT、N_T、D_T；保存每源属性及 `sum(V)`、`sum(Gamma)`、`sum(C*T)`。

- 同位拆分/倒序：上述场与物理总量保持；N_T/D_T 各自也保持。
- 全体 V 缩放：u、J、N_T、D_T、总量线性缩放；Tbar、gradT 不变。这检验 omega 与 Gamma 的解释，不能通过仅改变一个没进入核心的 metadata 字段替代。
- 输入和核心无旧 NX/layers/gain 依赖以源码/API 审计保证；不制造只改无用 metadata 的空洞数值测试。

### B. Gaussian kernel 与完整 Jacobian — 1 case

`kernel-analytic`：单源位置0、sigma=.07、Gamma=(0,0,.001)、V=.001、T=450。core事前选定 `qSwitch=.5`、F级数k=0..11共12项、D为同多项式导数。查询包括原点，以及 `q in {.01,.1,.25,nextafter(.5,0),.5,nextafter(.5,+inf),1,2,4,8}`、`d in {(1,0,0),(0,0,1),(2,-1,2)/3}` 的 `r=.07*q*d`，共31点；nextafter 使用 IEEE Float64 相邻值。保存 requestedQ、actualQ 和实际分支，至少轴向查询须确实覆盖switch上下与等号，不仅靠标签认定。等号归常规分支还是series由core在冻结配置中明确，双方在同点都须满足参考容差。

参考为第2节高精度公式；核对 u、每个 J 分量、trace(J)、旋向与原点极限。独立有限差分以 `h=sigma*1e-4` 和 `h/2` 对高精度速度函数取中心差分，核对 production J；不以有限差分替代解析参考。单向量 Gaussian 涡量通常不散度自由，本例只验证核算子，不是完整物理涡环。

### C. 真正无散初态、过滤后速度和求积收敛 — 4 cases

`field-n8`、`field-n16`、`field-n32`、`field-domain40`。定义向量势 `A_vec=(0,0,A*exp(-|r|²/(2a²)))`，`A=.01 m²/s`、`a=.1 m`、`r=x-c`，`u=curl(A_vec)`。其解析涡量为

\[
\omega=A e^{-|r|^2/(2a^2)}
\left({xz\over a^4},{yz\over a^4},{2\over a^2}-{x^2+y^2\over a^4}\right).
\]

前三条在 `c+[-.5,.5]^3` 用 n³ 中点：`xi=c+(-L+(k+.5)*dx)`，L=.5，dx=2L/n，V=dx³，Gamma=V*omega(xi)，固定 source sigma=.06，T=300，cV=3。125个内部查询 `c+.05*(a-2,b-2,d-2)`，a/b/d=0..4。仅 u 为本家族主指标；不运行 N² 粒子动力步。

连续参考是 **经过相同 Gaussian 过滤后的**

\[
u_\sigma(x)={A a^3\over(a^2+\sigma^2)^{5/2}}
e^{-|r|^2/[2(a^2+\sigma^2)]}(-y,x,0).
\]

不得与未过滤 u 比较后归咎于 solver。相对 L2 为 `sqrt(sum_q ||u_num-u_sigma||² / sum_q ||u_sigma||²)`；所有查询等权，包括参考恰为0的点，分母用全体和。

`field-domain40` 使用 L=.625、n=40，因此与 n32 **同 dx=.03125 且完整保留旧点**；新增外层源只测截断敏感性。此前 .5→.6 的非固定网距建议不采用，以免改变两种误差。输出 domain40 与 n32 的绝对/相对场差、各自对全空间参考误差；它是诊断，不另设 outcome gate。

独立 reference 自检：用 tensor Gauss–Hermite 16³及24³节点，对全空间 `E[u(x+sigma*Z)]`（Z 为标准正态）积分，核对该解析过滤公式。必须正确转换 physicists' Hermite 权重/节点；审计不得用直接复刻生产 Biot–Savart 求和代替这项检查。

### D. 温度梯度与浮力源单位 — 3 cases

`temperature-constant`：基础8源全部T=450；`temperature-linear-samples`：Ti=`450+40*pi_x-25*pi_y+30*pi_z`。两条使用基础64查询，保存 N_T、D_T、Tbar、gradT，独立高精度求和及 `h=1e-5 m,h/2` 的中心差分检查商法则。常量 Tbar=450、gradT=0；线性采样只要求与其 Shepard 场导数一致，不要求 gradT=(40,-25,30)。

`buoyancy-source-units`：在同8个位置，Gamma 初始全0；T0=300、DeltaT=100、b=.5 m/s²，连续温度使用上一条的线性函数，**本子测试注入已知 g=(40,-25,30) K/m**。dt=.01s，单次同步显式更新应有

`DeltaGamma_i=dt*Vi*b*(-30,0,40)/100`。

保存 base、all-split2、selective2、reverse 四种表示的 RHS/更新结果，按 anchor 求和。检查总 source 相同、单子源按 V 分摊；初始 u=0，位置在这一次显式步不动。这里只验证 RHS 单位/符号/时序，不证明用离散温度梯度驱动的完整浮力流动正确。

### E. 指定无散应变的时间阶 — 3 cases

`strain-dt010`、`strain-dt005`、`strain-dt0025`：一粒子 `x0=(.03,-.04,.05)`、V=.001、Gamma0=(0,0,.001)、sigma=.07、T=300；指定外部 `u_ext=D*x`、`D=diag(-.5,-.5,1) /s`。无浮力。自己的 u=0、`J_self*Gamma=0`；完整 RHS 加入外部 D。

终点 t=.1s，dt=.01/.005/.0025，精确步数10/20/40。每步同步 Forward Euler：`x_new=x_old+dt*D*x_old`，`Gamma_new=Gamma_old+dt*D*Gamma_old`。比较解析 `x(t)=exp(tD)x0`、`Gamma(t)=exp(tD)Gamma0`；另用独立离散闭式 `(I+dtD)^n` 核对每步。记录全部状态，不只终点。

### F. 周期均匀浮力的平均模式 ODE — 3 cases

`mean-dt010`、`mean-dt005`、`mean-dt0025`：同 x0、V、sigma，Gamma0=0、T=350、T0=300、DeltaT=100、b=.5，Umean0=0；t=.1s、步数同 E。均匀theta=.5，curl force=0，`a_mean=(0,.25,0) m/s²`。

规定同步显式时序：先用 **旧** Umean 更新位置，再 `Umean_new=Umean_old+dt*a_mean`；Gamma 始终0。连续参考为 `Umean=a_mean*t`、`x=x0+.5*a_mean*t²`；离散独立闭式为 `x_n=x0+.5*a_mean*dt²*n*(n-1)`。速度误差只应在舍入范围，不对其要求单调下降；位置误差一阶下降。本项只验证零模 ODE 与时序，不声称已实现 periodic kernel/压力投影。

## 5. 数值判定：执行有效与物理合同分别报告

所有 tolerance 在结果前固定；不得在失败后扩大。componentwise 基础比较用

`abs(candidate-reference) <= 1e-11 + 1e-10*max(abs(candidate),abs(reference))`。

不同单位的字段分别比较，不把 u、J、T、Gamma 混成一个范数。总量也采用上述双项容差，并保存实际误差；不要求接近0的量作 relative-only 检查。

| 检查 | 判定 |
| --- | --- |
| A/B 解析值、同位表示、V缩放、D高精度 N/D/T/grad、D源更新、E/F离散闭式 | 上述 componentwise tolerance；所有点/步均须满足。 |
| B 解析 J 的 divergence | `abs(trace(J)) <= 1e-11 + 1e-10*max(abs(J))`。 |
| B 独立速度有限差分 vs J | 两个 h 均 `maxabs(error) <= 1e-7 + 1e-6*maxabs(J_ref)`；不要求 roundoff 主导时误差还单调下降。 |
| C 真正空间加密 | n32相对L2≤.01，且 `error16<error8`、`error32<error16`。没有声称固定sigma趋近未滤波NS。 |
| C 解析过滤公式的 GH 自检 | 16³与24³各自、相互差异均以全125点相对L2≤1e-8，另保存最大绝对误差；reference失效则判审计无效，不用不稳定参考宣布核心成败。 |
| D 常量温度 | max abs(Tbar−450)≤1e-10K；max abs(gradT)≤1e-9K/m。 |
| D 商法则 vs 独立温度有限差分 | 两个 h 均逐分量 `abs(error)<=2e-6 K/m + 2e-6*abs(grad_ref)`。 |
| E 时间收敛 | x、Gamma 各自终点相对L2严格递减，fine≤2e-4；两次 error_coarse/error_fine 均在[1.8,2.2]。 |
| F 时间收敛 | Umean与Gamma按离散闭式容差；位置对连续参考的非零绝对误差严格递减，两次比值均在[1.8,2.2]。 |

只有输入覆盖、有限值、不可变性、输出/源码指纹和独立重算成立时 `executionValid=true`。数学门槛不通过是 `physicalContractPassed=false`，不能藏在“代码成功运行”。本轮不设置速度排名或加速 gate。

顺序：完整保存 A–C 三个静态家族的12 cases；若其有效但合同失败，停止 D–F，保留9条 planned cases 及明确 `stopped_after_static` 原因，不称21条全部完成。若静态通过，再完整执行 D–F；每家族内部不按有利结果删例。reference自身失败/不有限须报告 invalid，而不是科学 stop。

## 6. 独立审计与原始证据

冻结 protocol、fixture设计、core、runner、审计源码及依赖版本 SHA；记录操作系统、CPU、Node/Python版本。formal开始/结束验证源码和fixture清单一致。保存每case所有源、查询、所有原始u/J/T/grad/RHS、每步状态、计数与配置；JSON须保留Float64可往返精度，必要时另保存 little-endian Float64及SHA。不得仅存pass布尔或最终摘要。

独立 Python 审计应从原始fixture重建 V/Gamma、N/D、商法则、Gaussian erf/J、过滤连续场、GH reference和E/F闭式；不导入production core。B再以独立高精度u中心差分交叉核验J。取消消去的额外核参考可用 `F=sqrt(2/pi)/sigma³*integral_0^1 t² exp(-q²t²/2)dt`、`D=-sqrt(2/pi)/sigma⁵*integral_0^1 t⁴ exp(-q²t²/2)dt`，以GL32/64核验，并记录C家族独立直接和的实际coverage。每项误差同时保存最大值、对应ID和总体统计。拆分先按anchor汇总物理量；查询按固定ID对齐。

建议至少包含以下廉价审计故障注入（只对副本）：源Gamma漏乘V、J一个符号改变、温度漏归一sigma^-3、拆分后未分V、mean使用newU更新x、把过滤参考换成未过滤u；每项应被其对应门槛拒绝。它们检验检测能力，不是新增算法实验或新物理证据。

已实现的独立审计使用100位 Decimal 工作精度及 erf 级数1e-90终止（不是生产近似）。C额外直接和检查固定查询索引 `[0,12,24,50,62,74,100,112,124]`，即9/125点、每点全部源；GL32/64相互相对L2须≤1e-8才视该额外参考有效，GL64与production采用基础componentwise容差。主要空间收敛与GH自检仍覆盖全部125点。`audit_cases(records, static_only)`供runner作12/21条门控；CLI从保存文件另核manifest/raw/逐case/source SHA，拒绝覆盖已有输出。六项故障注入通过`--fault-injections`在完整保存数据的副本上运行，并要求对应未修改控制先通过。

## 7. 本机计算预算及解释上限

C主levels共 `(512+4096+32768)*125=4,672,000` source-query pairs；同dx扩域另 `64000*125=8,000,000`，合计12,672,000。不用32768²粒子互作用、不动态演化该云。独立 NumPy 可按query或source分块，避免同时分配12.7M×全部J分量；GH24³×125为1,728,000次独立解析u采样。其余case很小。可运行一次接线/资源预试确认内存与有限值，**不得依据误差结果改变参数或gate**；若受时间预算限制，记录未完成，不降精度冒充通过。

这些检查只使标准核/单位/指定ODE成为可信 baseline。没有演示长期涡动力收敛、黏性、壁面、燃烧、重建scene、与FieryGS同模型、质量–成本优势或系统创新。后续MAC/边界研究必须另立同方程/同过滤/同边界合同。

参考：[Winckelmans 等，1996](https://www.esaim-proc.org/articles/proc/pdf/1996/01/winckelm.pdf)；[FLOWVPM Gaussian核作者源码](https://github.com/byuflowlab/FLOWVPM.jl/blob/master/src/FLOWVPM_kernel.jl)；[FLOWUnsteady 理论](https://flow.byu.edu/FLOWUnsteady/theory/rvpm/)；[Fedkiw–Stam–Jensen，SIGGRAPH 2001](https://graphics.stanford.edu/papers/smoke/smoke.pdf)。本协议公式的具体推导与局限另见 `work/p5-physical-reference-review.md`，这些来源不是本项目新方法。
