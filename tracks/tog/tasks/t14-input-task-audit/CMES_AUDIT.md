# CMES family：输入与编辑任务资格审查

2026-10-27；按 [PROTOCOL](PROTOCOL.md) 完成两轮，随后停止。仅阅读出版正文及这一 family 的精确发布检索；零训练、模拟、安装、外联或大型资产下载。访问明细见 [cmes-access.json](cmes-access.json)。

**判定：本轮 no-go——尚无合格输入/任务可进入数值准备；部分发布条件 unknown。** 这不是因缺两个现成 checkpoint 就否决。可重现的普通多初始化 recipe 也可能支持后续准备；但本篇目前能核实的是重建 ensemble，未建立共同续算干预和可评价的具体编辑决定。不能据此否定一般反事实研究，更不能因未搜到代码就断言代码不存在。

## 实际发表了什么

Lian 等，*Uncertainty-Aware Physical Simulation of Neural Radiance Fields for Fluids*，CMES **140(1), 1143–1163 (2024)**，2024-04-16 出版，[DOI/出版全文](https://www.techscience.com/CMES/v140n1/56211/html)。本轮实读 §3.1–3.3、§4.1–4.2、§5、数据声明和参考文献中的数据来源；未只依据摘要。

| 核查项 | 原文定位及实际支持 | 未能据此确认的事项 |
|---|---|---|
| 观测与训练 | [§4.1](https://www.techscience.com/CMES/v140n1/56211/html)：ScalarFlow 五固定相机、120°弧，单视角 120 帧约 4 s，共 600 张图；1024 像素/次、600k iterations，报告 RTX 3090。§3.1/3.2 给出频率正则、残差网络和激活构造。 | 未核到本实验序列 ID、确切图像/相机包路径、完整可执行配置、ensemble 成员数/权重发布；600k 不是训练 wall time。ScalarFlow 被引用不等于本 CMES ensemble 已交付。 |
| ensemble 操作 | [§3.3，式22–25](https://www.techscience.com/CMES/v140n1/56211/html)：相同数据、不同初始网络权重；NeRF 预测颜色/密度，多个 PINN 基于密度推断速度；统计均值与离散程度。 | 同训练集不等于每成员通过同一逐帧观测容差，也不等于独立后验样本或校准覆盖区间。本轮未检查到可逐成员重放的状态。 |
| 输出及时间 | §3.1 式2、§3.2 式20：时空坐标到颜色/密度、三维速度；§4.1 展示重建视频、速度/涡量 HSV 图及 PSNR，§4.2 展示不确定性统计。文中另述 30 帧/1 s 渲染。 | 没有核实含 pressure、source、边界状态、积分器状态的续算 checkpoint；重建时间查询/重渲染不能自动读作从新初态推进。30 帧展示与原 120 帧的具体时间裁剪关系未知。 |
| 单位与物理合同 | §3.1 位置编码使用归一化坐标；§3.2 将 optical density 与 smoke concentration 视为成比例，并称 velocity PINN 不需边界条件输入。式21写出对流/散度损失。 | 不能把归一化速度当 m/s；未核到物理长度/时间映射、密度比例常数、续算 BC/source 参数。式18提到 pressure/Re/body force，不等于式20输出这些量，亦不等于已交付完整新干预求解器。 |
| 改稿/续算 | §4 的实际结果是重建及统计；[§5](https://www.techscience.com/CMES/v140n1/56211/html) 将 robust engineering applications 等列为未来工作。 | 未见本 family 实演两成员施加同一风/障碍/源编辑后的再积分，也未见“选择哪个编辑”的目标、代价或验收。§3.3 泛述 NeRF 可操纵外观，不是具体续算编辑接口。 |

这是直接相关的已发表 ensemble 先例，不能把“多个观测拟合产生不同物理预测”本身再包装为贡献。但其已有重建/统计能力与 T14 要求的干预后编辑决定也不能混同。

## 发布与可访问性

- 出版 HTML 可完整访问；文章标 **CC BY 4.0**。该许可不能自动延伸到未检得的代码、训练 checkpoint 或 ScalarFlow 数据。本文仅存分析与小型访问元数据，未把论文复制进仓库。
- `Availability of Data and Materials`（正文结论后）提供的是自建 simulation script、Blender 渲染、导出 camera poses、调整 loader 的四步概述；没有给出作者仓库、成员模型、实验输入下载 URL 或代码路径。**代码路径：未核实；checkpoint/data release：unknown；对应资产许可：unknown。** 不把这段概述称为可直接运行的释放包，也不声称无法重现。
- 第二轮仅用题名/DOI 加 code、data、supplement、checkpoint 精确检索。结果命中出版正文、PDF和书目索引，未核实作者资源入口。ScienceDirect 同文镜像直接访问返回 403；这是该路线访问失败，不是“没有附件”的证据。没有继续搜索第三来源 family，也没有跟随不相关推荐。

## 为什么本轮不进入计算

支持条件目前是 **recipe-only/部分记录**，不是已认证的 continuation-ready ensemble。即使之后拿到 ScalarFlow 原图并按普通多初始化训练，也仍须明确：各成员的共同观测验收、共同状态/单位/边界导出、同一干预，以及会改变的具体创作选择。论文没有给出最后两项的实际实例或创作者要求；不能将研究人员另拟的要求归给论文作者。研究人员定义新任务是允许的，但它仍需独立的操作理由与可评价交付。

因此下一缺口是**任务和干预合同**，不只是下载。若将来得到作者给定的可续算示例或独立、来源清楚的编辑 brief，可另行资格化；本次不以自造风/ROI、再训练 ensemble 或新优化器填补。这个 no-go 只关闭当前 CMES family 的计算入口，不推断未知资源不存在、不推断问题不可能，亦不把来源存在视为 TOG 核心贡献。
