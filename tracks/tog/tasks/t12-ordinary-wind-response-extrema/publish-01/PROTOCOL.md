# T12 普通风响应极值见证搜索（执行前）

只使用已知非对称合成密度和同一公开reference seed。目标是在完整20帧8bit观测的量化区间以及实际初始细网格速度先验内，寻找同一局部风干预的较大/较小响应。搜索结果只是实际找到的合格见证，不是全局极值、置信区间、新算法或真实案例。旧T02–T11不改；不读旧优化控制。

## 数值与数据

原core SHA固定为`ac750b70a86743ac858f1c53cf620ce29c63c462456115af4d0d8c93fa20bd9e`。32³、float64、dt=.025，原20°相机32²×64深度→64²；周期MAC被动密度，无燃烧/浮力。已去除witness配方的scene.initial_state只提供rho，返回的速度丢弃；这项设置成本计入setup。

theta为3×8³粗MAC变量，reference三分量为[.125 sin(2πy_face), .10 sin(2πz_face), .125 sin(2πx_face)]。实际初始速度`v0=P(interpMAC(.2*tanh(theta)))+(0,.12,0)`。只有该实际v0受max分量≤.35及sqrt(mean全部3×32³分量平方)≤.18限制；不以粗系数界替代它。所有完整历史/未来状态另过finite、rho≥−1e−12、alpha∈[−1e−12,1+1e−12]及散度inf≤1e−10。

reference从该seed完整计算一次20历史+2×20未来（60step），公开原浮点观测、`floor(255*alpha+.5)` uint8观测和实际状态/输入，费用列setup。已知rho、原模型和这一个seed对两极相同。量化区间为[max(0,(code−.5)/255),min(1,(code+.5)/255)]，验收允许1e−10 alpha误差；实际重新量化byteExact与逐码差计数单独描述，不称容差区间通过就逐码相同。

局部风取z-edge坐标(i,j,k+.5)/n上的`Az=d_y(.45)*exp(-Σd(center)^2/(2*.12²))`，center=(.32,.45,.43)，d是周期最短差。`fx=D_y+Az, fy=−D_x+Az, fz=0`，统一缩放至max分量.35。该场是周期尾部非零的离散curl，不声称严格紧支撑。future更新0..9施加该力，10..19置0；另一支全程零力。core先平流后加力，所以future1的密度/图像尚不受风影响。每次完整eval只推进共享历史一次，再分别推进两支，共60step。

`g`只用future20（绝对step40）alpha的半开ROI[28,26,36,56]像素和，除以固定reference obs20全图alpha总和。`d=g_wind−g_no_wind`。最小臂优化+100d，最大臂优化−100d，无额外正则或第三个目标。

## 普通求解器及预算

PHR约束完整保留全部像素上下界：`255*(lower-alpha),255*(alpha-upper)`，再加`max(abs(v0))/.35−1`与`mean(v0²)/.18²−1`，共163842项。PHR按SUM累加，不mean。lambda=0、mu=1；至多3外轮，每轮最多12个L-BFGS返回步；strong_wolfe/max_iter1/history10等参数见config。外轮更新lambda=max(0,lambda+mu*c)，若max正违反量未减半，mu乘10上限100；每外轮重置历史。两极从同一seed独立开始，不互喂求解结果。

每极≤80次真实完整eval，包含seed初验、closure/线搜索、验收cache miss与强制末验。仅缓存返回输出的detach clone；必须theta快照torch.equal且固定输入身份一致才复用，否则实算。torch.equal是数值相等，不声称signed-zero逐字节相等。closure预留可能的验收miss与末验两个slot；预算/软时限中断时恢复最近优化器返回点，不把trial说成accepted。

本任务寻找存在性见证，**所有实际完整评估且通过全部门的点（包括line-search trial）都可成为best**；记录evaluation ID和origin，明确其是否是优化器返回点。seed本身是候选；没有新合格点就返回seed。best在结束时另付一次真实完整eval检验，计入80。不给seed质量通过即提前停止，也不按响应幅度设成功阈值。每极300秒软上限（停止开始新搜索eval，仍须末验）；整个worker900秒硬上限，超时保留已有结果，不自动重试或降规模。

## 新G0与内存门

资格x=seed+.01×固定CPU Torch Rademacher(seed2026102712)。两方向取独立连续发生器seed2026102713的Rademacher并以元素平方和开方归一到Euclidean L2=1。固定h=1e−5、1e−6。1个AD完整eval+8个FD完整eval，共9forward；同AD图分别求d与完整`100d+PHR_SUM`梯度，计2reverse。资格lambda全2、mu1固定；记录PHR分支活跃数与距零余量，不要求全部分支活跃。

每个标量/方向/h的`abs(FD−grad·dir)/max(abs(grad·dir),1e−8)≤1e−4`，全部有限。此次新资格不复用T04/T08旧G0。G0实测Torch allocator峰值allocated≤6GiB、reserved≤7GiB；OOM或资格失败停止，不自动checkpoint/降低分辨率/改变h。allocator统计不是完整进程GPU峰值。

## 记录

默认stdlib plan，不导入Torch；root审查后才可freeze/execute。独立子进程MKL sequential、4threads、固定RTX UUID，900秒监督，不安装依赖。原始runs忽略Git。保存reference/G0输入与输出、逐eval/返回步精简JSON、每极最佳见证及末验NPZ（theta、初始v、raw帧与末v/rho、约束），不重复保存全部优化历史。所有真实eval/step/reverse、cache hit/miss、候选来源、source/input首尾SHA和成本完整披露。普通缓存、AL、参考seed及尝试成本均不当作新贡献。
