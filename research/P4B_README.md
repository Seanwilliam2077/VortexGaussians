# P4b：动态热交换与 native 3D VPM 接线检查

本轮把 P4a 的显式有限热容交换接到实际 native 三维 VPM，采用 64 个固定气体 parcel、32 个固定 surface 物理点、1 s 的合成工况。热反馈可以改变动力，运动可以改变下一步交换图。它是标准参考接口的验证，不是燃烧模型、候选新方法、渲染评测或性能 benchmark。

方法、完整 12 例矩阵和门槛见 [P4B_PROTOCOL.md](P4B_PROTOCOL.md)，精确输入见 [p4b-design.mjs](p4b-design.mjs)。不要从 quick 的短时结果推断 full 的因果暴露或时间细化结果。

## 运行

在仓库根目录使用 Node.js。runner 采用已有浏览器研究 harness，需可用 Chromium/Chrome/Edge 可执行文件；与既有实验使用相同环境。

```powershell
node --test research/tests/p4b.test.mjs
node research/p4b-run.mjs --suite quick --out research/runs/p4b-quick
node research/p4b-run.mjs --suite all --out research/runs/p4b-full
```

如需要显式指定浏览器：

```powershell
node research/p4b-run.mjs --suite all --out research/runs/p4b-full --browser-executable 'C:\path\to\browser.exe'
```

运行前后保存研究源码指纹。本轮没有独立 smoke 脚本：8 例 quick 用于浏览器接线预检，另执行 unit 与旧默认/P3 回归，再由 root 启动正式矩阵；不要在一个正式 run 中修改源码。结果保存在独立目录，不覆盖既有 P4a/P3 原始证据。

## 证据如何解释

- 交换守恒只指 `sum(C*T)` 的显热。现有 VPM 浮力/阻尼/限幅没有机械能对等账，不能称总能量守恒。
- 64 个稳定 gas ID 的最终位置 RMS 超过 1e-6 m，和全部 96 热节点的最终容量加权温度 RMSE 超过 1e-6 K，是两个机制暴露条件；它们不衡量真实火焰准确性。
- native 积分复算使用保存的实际树场输出，因此能检验温度接线、Float32 存储、声明积分公式；它不是另一套独立流体 solver 的验证。
- dt60/dt120 对 dt240 的差是时间细化诊断。最细结果不是物理真值，协议不预设误差严格单调。
- 相机、额外 snapshot 和输入 reverse 必须保持同 arm 完整回放。不同 exchange/feedback arm 的 Kelvin、配置与计数可以不同，不能误要求其 fullStateHash 相同。

关键原始数据是每个 outer step 的热态、容量、当前几何、热图/借贷、实际 packed 与 field 量、气体积分前后状态、稳定 ID 和域检查。独立 Python 审计从这些记录复算；只看最终 hash 或净借贷自消都不足以确认正确性。

边界夹持、Morton/transport 出域或 native would-retire 使对应运行 invalid，不能以总显热仍守恒掩盖。梯度、涡量和速度限幅是声明的原模型操作，分别记录并复算，不因发生而事后删掉 case。

## 仍未覆盖的研究问题

没有燃料/氧气/反应热、出生退役、烟质量、真实材料、障碍物、实景测度推断、图像质量或运行速度结论。surface 物理点就是独立材料 proxy；当前没有与它竞争的新 candidate。即使本轮全部通过，也必须另有可证伪的方法优势及公平强基线，才能支撑投稿贡献。
