# 可燃的数字记忆（暂定） · 艺术排练入口

## 2026-10-31 current: A36 two-line handover material sample

[A35](studies/a35-reading-by-fire/CREATOR_CHOICE.md) selected an original fictional station handover note, 《末班之后》; [root accepted](studies/a35-reading-by-fire/DECISION.md) one material qualification before a full work. [A36](studies/a36-handover-material/BRIEF.md) fixes two lines, nominal 32px type/48px spacing, the original material and legacy budgets, one ignition and 360 steps. Implementation is in progress; no new run, image or score yet. A fixed reviewer's [pre-production consultation](studies/a36-handover-material/REVIEWER_CONSULTATION.md) identifies a reading relation and the decorative-highlighting counterreading without grading unseen work. A32 remains closed at independent 3/6 and 4/6; A33 no-selection, A34 direct-source scope and older results remain. Overall 5/6 unmet; TOG/main unchanged, full goal active.


**2026-10-30：A14封存为试作，结束当前投稿核心路线。** [A18有限比较](studies/a18-context-positioning/README.md)与[独立复核](../validation/art-a18-core-decision.md)认为，轮流移动、接续变化和共同退开虽有图像依据，现有形式仍未支持其核心艺术认识。维持第二轮总体3/6、准备度6/10、置信度4/5；不是因录像失败否定作品，也不据来源缺失否定领域。原平台和艺术线继续。[A19](studies/a19-artistic-commitment/BRIEF.md)先完成一页单案创作决定，选择具体对象、观看关系和观者行为/取舍，暂不制作或运行。A15/A16失败与[A17实际33图](studies/a17-saved-sequence-reading/README.md)保留，补录循环关闭；总体5/6目标未达。

首个作者排练原型。它把现有 VortexGaussians demo 放在“保存的空间 → 介入燃烧 → 重置重看”的三个阶段中，并记录创作选择。它不是完成作品、观众实验或新燃烧算法。创作命题及待补证据见 [ART_BRIEF.md](ART_BRIEF.md)；技术证据另见 [research/EVIDENCE_STATUS.md](../../research/EVIDENCE_STATUS.md)。

目前还没有实际人类作者体验记录。此前的 [A07《一次重新开始》](studies/a07-return-and-record/run-01/study.mp4)为24.92秒、四镜头，从原状、燃烧到重置，结尾让恢复场景与真实操作摘要同屏。这是 agent 提出的完整观看顺序，合成示例、静帧和并置均有标记；它没有替作者选择个人故事或证明艺术效果。[制作说明](studies/a07-return-and-record/README.md)保留剪辑计划、元数据读取失败及后置验证；[独立完整解码检查](../validation/a07-delivery-review.md)确认 623 帧成片可读。

来源是 [A06 十秒燃烧与重置](studies/a06-char-and-reset/README.md)：原参数下一次播放到 10.00 模拟秒，计数为 3,320 个燃烧点、1,400 个燃尽点；火焰根部只有局部可见深色痕迹，重置后消失。27.609 秒完整采样录像保留实际操作。这里的焦化是模型状态及着色，未删除点云几何；回执保存摘要，不能恢复烧损状态或代替个人记忆。

较早的 [A04 一秒自动演示](studies/a04-automated-score/README.md)与 [A05 三镜头剪辑](studies/a05-reset-score/README.md)继续保留，连同首试依赖失败及来源记录。各版均未填写创作笔记，也未修改原页面或模型。

## 启动

不需要 npm 或构建。在仓库根目录运行普通本地静态服务：

```powershell
python -m http.server 8000 --bind 127.0.0.1
```

然后打开 <http://127.0.0.1:8000/tracks/art/>。首次打开只显示导览和笔记，点击“载入合成示例”才创建原 demo。需要支持 WebGL2 的浏览器。直接双击 HTML 的 `file://` 同源／fetch 限制可能阻止连接；出现错误时按上述方式打开。关闭终端中的静态服务即可停止服务；本页不自行安装或启动服务。

入口引用 `../../demo/index.html?embed=1&solver=vpm&orbit=0`，**没有修改或复制原 demo**。右上角可以另开原 demo，但独立窗口的操作不会进入排练日志。

## 三阶段操作

1. **保存的空间**：载入仓库合成 `static/test_scene.ply`，或选择有权使用的本地 PLY。示例不是实拍记忆。初始暂停、无外部火源；可旋转观看并写下情境。每文件上限 64 MiB，原读取器最多保留 800,000 点，页面显示实际保留／原点数。大文件或不兼容资产可另开原 demo；本入口不提供格式转换。自选文件不会上传，真实捕获身份与授权仍需作者说明。
2. **介入燃烧**：初始点火位置 `(0, 0.65, 0)`、半径 `0.30` 适合合成示例。载入使用原 auto-fit 比例，并将场景 lift 设为 `0.6`；坐标不是实景米制。点火按钮显示实际新点燃数，未命中会明确报告。随后选择推进 1 秒或播放 10 秒，均用原 `step(1, 1/60)`，每显示帧最多推进一步；可能慢于墙钟。不会自动续段。切阶段、隐藏或离开页面会暂停。
3. **重置重看**：先记录变化，再显式点击重新初始化。原 `reset(seed)` 清空当前流动及场景烧损，保留场景几何、当前观看角度和本页笔记。**它不是精确逆燃烧，不恢复此前完整物理状态，也不倒放历史。** 固定种子 `20261027` 不构成跨浏览器或跨平台逐位保证。

相机 slider 仅暂停时可用，度数转换为原 `P.yaw = degrees / 180`（原相机随后乘 π）。换视角会改变原分层模型的世界耦合，不能用本页面主张视角无关物理。原模型的燃料、热量、炭化与传播参数是启发式视觉控制；公开计数不是真实损毁或热量测量。

### 追加原型：重置前操作回执

显式重新初始化后，画面下方展示最近保留的该次操作前的场景、模拟时长与两项模型计数。“暂时收起 / 再次展开”只改变卡片呈现，不删日志、不改当前状态；刷新可保留这项显示选择，但不会恢复仿真。没有重置就不生成这类回执。它来自原有操作日志，不是新增烧损存档、持久物质记忆或观众解释。候选问题、反例和排练模板见 [PROTOTYPE_02.md](PROTOTYPE_02.md)。

## 笔记与数据

- 三种性质分别为作者草稿、作者观察、真实观众记录。默认是作者草稿。选观众记录时必须填写实际观看情境和观察，工具仍不会认证其真实性；没有观众时不能据此生成观众结论。
- 表单草稿与保存记录使用当前站点的 `localStorage`，键为 `vortex-gaussians.art.memory.v1`。同源和浏览器配置不同会得到不同本地记录；隐私模式／配额可能使保存失败。错误会在界面显示，读取失败的旧记录不会被自动覆盖。
- 导出 JSON 含创作记录、当前草稿、时间与阶段、有限公开计数／参数、文件名与可用时的 SHA-256、操作日志。不含 PLY 原数据、截图、粒子状态或可续算 checkpoint。刷新页面不会恢复已燃烧状态。无服务器上传或外部分析服务。
- 最多 200 条笔记；达到上限不会静默删除。操作日志最多 1,200 项，超出会保留最新项目并累计 `omittedEventCount`，因此不是无限完整事件历史。
- 请定期导出备份；清除浏览器站点数据会丢失记录。观众内容只使用经同意的匿名记录，不在笔记中收集姓名或联系方式。

## 使用的公开 API

| 接口 | 本入口用途 |
| --- | --- |
| `__demo.P` | 关闭外部 emitter、暂停／spread 标志、场景变换和观看角度；其他求解／显示默认保持原实现 |
| `loadPLY(buffer)` | 原解析器载入本地或仓库示例；读取 `kept/total` |
| `reset(seed)` | 新排练起点；重建场景烧损状态 |
| `ignite(x,y,z,r)` | 返回实际新点燃个数 |
| `step(1,1/60)` / `render()` | 显式有限步进和原渲染；步进期间临时 `paused=false`，随后恢复 true，以保留原 ember 路径 |
| `spreadInfo()` / `sceneN` | 界面有限状态计数及笔记元数据；不伪称完整状态认证 |

不调用原研究模块的数值内核，不使用 `warm()`、`bench()` 或隐藏自动模拟。原 iframe 在 embed 模式中不会自行推进；只有作者显式请求的本段步数被执行。

## 只通过界面的冒烟检查

以下保留为复测清单；**本轮实际执行范围见文末，未执行项不按通过计**。可用现有 Playwright 访问上面的 HTTP URL，仅通过可见按钮／表单操作；不要 `evaluate(__demo...)` 注入状态来代替 UI。控制效果可读可见计数／时间；导出内容可通过 download 读取。

1. 打开页面，确认未载入、模拟时间为 0，点火／推进按钮在尚无场景时不可用。窄屏检查阶段、笔记与按钮没有遮挡。
2. 点击“载入合成示例”，等待状态报告载入 **45,808 / 45,808** 点；确认标记“合成／非实拍”、燃烧和炭化为 0，画面可见。观察数秒时间仍为 0。
3. 在“保存的空间”写一条作者草稿并保存。切第二阶段，点击默认位置点火；界面应报告非零新点燃数，时间仍为 0。点击“推进 1 秒”，应最终为 1.00 s 并自动暂停；不要把这一等待时间当性能测量。
4. 点击“播放 10 秒”，推进后点击暂停，记录可见时间。等候时它不应继续变动。再次播放并切第三阶段，也应暂停；浏览器切走标签应暂停。
5. 第三阶段重新初始化：时间归零、燃烧／炭化为 0，原笔记还在；不是倒放。重新载入场景后 slider 与角度标签归零。暂停时把角度调到 60°，检查其标签和画面响应，不能称独立物理相机认证。
6. 选择观众记录但留空情境或观察，保存应拒绝并解释。填写匿名实际情境才允许保存；如检查人员仅试功能，请改选作者草稿，勿留下伪观众记录。
7. 导出 JSON，核 `schema`、`version`、阶段、作者记录、资产合成标记、点火个数和初始化事件。刷新后笔记／草稿应可恢复，但场景必须重新载入，不能自动恢复燃烧。
8. 用本地 PLY 文件选择入口载入合法文件，或用不兼容小文件检验明确失败；不需要新增或上传第三方资产。记录所测浏览器与视口，报告检查范围及任何失败。

## 投稿语境

截至 **2026-10-27**，[SIGGRAPH 2027 Art Papers 官方页](https://s2027.siggraph.org/program/art-papers/)说明接收论文发表于 **PACMCGIT** 的 SIGGRAPH 2027 Art Papers 专刊；Long／Short 截止均为 **2027-01-19 22:00 UTC**（北京时间 **1 月 20 日 06:00**），详细投稿要求尚待发布。这不是 TOG Technical Papers 同一发表轨道，也不意味着当前原型已达到艺术论文要求。

## 本轮实际检查记录

2026-10-27 **加入回执功能前的首版**两类检查原记录分别保留，不互相替代，也不冒称覆盖后加功能：

- **无 GPU 页面壳检查：10 项通过。** 覆盖阶段切换、笔记安全显示与刷新持久、拒绝缺情境的观众记录、实际 JSON 下载等；未请求 demo、PLY 或 WebGL。见[集成审查](../evidence/INTEGRATION_REVIEW.md)与[原始检查记录](../evidence/checks/html.json)。
- **实际 WebGL 界面检查：13 项通过。** Headless Edge 149 通过可见按钮和表单操作，载入合成示例 45,808 点，默认点火 2,483 点，推进 60 步后在 1 秒模拟时间暂停；暂停、切阶段、重新初始化、笔记／导出、60° 角度元数据和本地 PLY 入口均通过，无页面异常。截图已目视确认火焰可见，390 px 窄屏无横向溢出。见[检查说明与截图](../validation/README.md)、[原始结果](../validation/art-ui-20261027/result.json)及[推进后画面](../validation/art-ui-20261027/after-one-second.png)。

隐藏标签暂停和跨浏览器行为尚未实测。这些是功能检查，不是性能／物理质量测试，也不是作品完成度或观众效果证据；首版检查导出的记录明确是自动化界面测试草稿。下一步艺术研究需要作品选择及实际作者排练；若主张真实地点的记忆，还需明确与该地点的关系，不能用检查项数量替代。

**追加回执功能检查：8 项通过。** Headless Edge 149 中，合成示例推进到 1 秒时可见燃烧计数为 3,746，重新初始化后当前时间与计数为零，回执仍显示此前的 1 秒和 3,746；收起、展开、实际导出、刷新及 390 px 窄屏行为符合合同，0 页面异常，受检源码前后相同。宽／窄截图均已目视检查。见[新结果](checks/reset-receipt-20261027-02/result.json)、[宽屏回执](checks/reset-receipt-20261027-02/receipt-wide.png)、[窄屏回执](checks/reset-receipt-20261027-02/receipt-narrow.png)。计数仅是本次实际读数，不成为跨运行恒定值的承诺。

第一次尝试在浏览器启动前因未配置现有 Playwright 模块路径失败（0 检查、未加载 WebGL），[失败记录保留](checks/reset-receipt-20261027/result.json)。仅为新子进程指定已安装模块路径后，用相同源码在新目录重测，没有安装依赖或更改判据。可在仓库根目录设置 `PLAYWRIGHT_MODULE` 指向本机已安装的 `playwright` 模块，再执行 `node tracks/art/receipt-ui.mjs tracks/art/checks/<fresh-name>`。浏览器和临时 HTTP 服务结束时关闭。此检查没有作者／观众体验记录，JSON 的 notes 为空。
