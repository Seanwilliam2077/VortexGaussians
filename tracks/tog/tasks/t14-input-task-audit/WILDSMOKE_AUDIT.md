# WildSmoke：有编辑演示，尚未取得合格的歧义任务输入

2026-10-27。完成两轮限定检查；无模拟、训练、安装、大资产下载或外联。
**本 family 当前为 `NO_QUALIFIED_INPUT_TASK`，并非资源不存在或 R19-B 不可能。**
公开 checkpoint 的存在已经确认；不足的是可复核的状态接续合同、共同观测下的重建配方，以及会改变实际编辑决定的评价任务。没有现成状态 pair 本身不是否决理由。

## 已发表操作与普通强路径

所读版本为 [arXiv:2509.11114v1](https://arxiv.org/html/2509.11114v1)（2025-09-14）；[当前版本页](https://arxiv.org/abs/2509.11114)仅列 v1。§3.5 将 visual particles 映成密度、physical particles 映成速度，再交给 PhiFlow；§4.4/Fig.8 从 Pixabay city 重建末帧开始，展示全局风、局部球形风域和刚性球障碍。给定风为 `(0.005,0,0)`，局部半径30；球半径10、文中中心只写 `(50,70)`，图为沿 Z 看 XY。图中仿真时间区别于原视频帧号。§4.1/4.3 的图像重建、自然未来预测指标不等于这些新干预的真实结果或任务决策验证。

这已经是作者公开展示的“重建资产→施加风/障碍→接续显示”，不能把实现同一操作本身称新增能力。若获得原接口，首个普通强基线应是作者相同初始化和干预下的完整 PhiFlow 重模拟，并计入恢复/转网格/模拟/显示；本轮未执行，不能编造速度、质量或可复现成功。固定镜头只需外观时，仍不能未经 brief 就强加物理接续要求。

## 输入与实现资格

| 项目 | 实际证据 | 边界／未解决项 |
|---|---|---|
| 代码入口 | [作者项目](https://autumnyq.github.io/WildSmoke/)的 Code 按钮文字仍为 `Code coming soon`，链接是[组织页](https://github.com/delta-lab-ai/)。定向检索与直接入口未定位 WildSmoke 专用脚本。 | 无可核 WildSmoke commit、wind/ball 函数行号或锁定依赖版本；不把“本次未定位”写成不存在。组织内 FluidGaussian 的 README 是另一篇论文，未扩展审查它。 |
| 演示媒体 | 项目 HTML 指向 `static/videos/city.mp4` 和 `static/videos/simulation_results.mp4`；本次只检查链接，没有下载或逐帧评估。 | 作者演示不等于原始监督帧、相机文件或创作者需求；不据页面标题宣称视频内容已目视复核。 |
| 公开资产 | [HF 固定版本](https://huggingface.co/datasets/delta-lab-ai/WildSmoke/tree/3e86196cf13b73c8e6a33c7c0c48b7e8d450bf9d)当前公开、未 gated；`Gaussians_ckpt.zip` 102,042,106 B，`city_vdb_out.zip` 1,833,979,888 B。 | 本轮仅取元数据，不下载 ZIP/VDB。后者的字段、体素变换和速度内容本轮未知，不能凭文件名补合同。 |
| 已有本地 checkpoint 证据 | 复用已封存 R13 静态报告：240帧、19字段族、4560有限非 object NPY+241JSON。physical xyz/velocity 为 N×3，visual xyz/scales 为 M×3、rotation M×4、color/opacity M×1；两层 visual_xyz 相同。`scale_factor=100`、`secs=.033`。 | 两层不是两个独立重建；physical/visual 也不是 ensemble。已有存储核验不等于本轮运行接续器；未知真实米/秒、摄像机标定与实际干预地面真值。 |
| 状态→网格接口 | v1 §3.5 Eq.3–5 给出 Gaussian 密度加权、归一化速度加权（分母 ε=1e−8）及共同 visual 包围域；随后 MacCormack 平流、压力投影。 | 未核实现的物理核宽、网格形状/轴序/采样点、长度缩放、velocity 换算、dt、边界、源项、force 时序、球完整3D坐标、pressure 设置。不擅用 PhiFlow 默认值补齐。 |
| 观测与多初始化配方 | 论文说明单视频、估计相机，以及生成视图/扰动视角参与监督；项目有可浏览演示媒体。 | HF 当前发布目录没有相机/处理后监督数据/训练入口。论文高层流程尚不足以确认普通 multi-init 能在同一可检查观测合同下产生可接续状态；这是 recipe-only 仍未核实，不要求预先存在两个 checkpoint。 |
| 许可 | 论文 HTML 标 CC BY 4.0；[HF card](https://huggingface.co/datasets/delta-lab-ai/WildSmoke)为空，API 无 license/cardData，当前 tree 无 README/LICENSE。[未合并的 card PR](https://huggingface.co/datasets/delta-lab-ai/WildSmoke/discussions/1)仅提论文/项目/任务分类。 | 论文许可不能自动覆盖 checkpoint、VDB 或原视频。原文提 Pixabay 通用来源许可，不能据此推断所有衍生资产再分发权；本轮无第三方代码/资产入仓。 |

## 已知上游先例不能替代 WildSmoke 实现

本轮 HF `main` 仍是 R13 的同一提交 `3e86196cf13b73c8e6a33c7c0c48b7e8d450bf9d`；三文件清单与其大小/LFS摘要相同，当前708 B tree JSON 的 SHA256 也仍为 `73f3ea23eca62d8747626fc2d544129f3074b77e9e88c9fefc24eef19c835b84`。这不是新发布或新资产进展。字段形状、JSON配置和 ZIP 内无相机/许可证来自旧 R13 完整检查；本轮未打开 ZIP/VDB，也未重新验证内部字段。本轮新增工作仅为发布入口复查与 state→sim／任务资格判断。

本机 R13/R15 已读的 FluidNexus 提交 `648dc6d922bd80f46881ba9452d24381692f240a` 是**条件解码先例**，没有新下载/运行：

- [`gm_fluid.py` L1654–1744](https://github.com/ueoo/FluidNexus/blob/648dc6d922bd80f46881ba9452d24381692f240a/FluidDynamics/gaussian_splatting/gm_fluid.py#L1654-L1744)保存 xyz 除 scale、velocity 原样；若 WildSmoke 保留它，场景坐标速度应除100，`.033`仍仅代码步长而非已校准真实时间。
- [L219–233](https://github.com/ueoo/FluidNexus/blob/648dc6d922bd80f46881ba9452d24381692f240a/FluidDynamics/gaussian_splatting/gm_fluid.py#L219-L233)对 raw scale/opacity 使用 exp/sigmoid，rotation 归一化；不能直接把负 raw opacity 当密度，也不能把 JSON 的浮力 `alpha` 当视觉 opacity。
- [L1177–1195](https://github.com/ueoo/FluidNexus/blob/648dc6d922bd80f46881ba9452d24381692f240a/FluidDynamics/gaussian_splatting/gm_fluid.py#L1177-L1195)确认后速度来自位移，限定保存相位；它不能证明 WildSmoke 使用同一调用路径，更不能替代其 PhiFlow 导入代码。

既有本地依据：`work/research-round13/INDEPENDENT_AUDIT.md`、`SCHEMA_PRECEDENT.md` 和 `work/research-round15/SOURCE_PHASE_REVIEW.md`。本次只读这些报告，不重复数组检查，也不把原始存储通过升级成作者动力学复现通过。

## 决策

具体持续编辑操作**有**；公开状态容器**有**；但可复现 observation→state→intervention 全链目前**未核定**，更没有经说明的“应该选择哪种风／是否会破坏批准区域”等创作者决定、评价阈值或控制干预真值。论文作者的定性烟雾偏转演示不足以自动建立后者；把保护对象/ROI临时加进去会是新的研究人员任务，不能称来源已有需求。

因此不从这份资产立即启动多初值优化、接续重模拟或新不确定性算法。即使未来补到单一可运行编辑器，仍须说明为何观测兼容状态分歧会改变某项可评价交付，而不只是得到非零差图。反之，若未来有共同监督、可复现多初始化配方、同一干预和具体决定，就无需先拥有现成 pair 才能准备任务。两轮预算现已结束；未知项保持未知，不追加第三 family。

访问范围、失败路由、固定版本和有界元数据字节数见 `wildsmoke-access.json`。未将搜索命中摘要用作实现证据；GitHub API 的403仅为该路由限流，HF API经普通有界HTTP成功，不混作资源缺失。
