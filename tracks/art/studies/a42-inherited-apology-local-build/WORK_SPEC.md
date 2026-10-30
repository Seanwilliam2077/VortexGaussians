# A42：道歉沿用的单次材料检查页

2026-10-31。执行前固定的实现说明。此页落实 [A42 BRIEF](BRIEF.md) 与其明确继承的 [A41 材料合同](../a41-inherited-apology-material/BRIEF.md)，回应 [A40 创作选择](../a40-material-handover-choice/CREATOR_CHOICE.md)。它是材料仪器，尚不是完整作品、论文或评分请求。桥接通过不能推出可见材料资格通过。

## 静态可行性与装配边界

原 `demo/index.html` 的整个脚本位于 282–4916 行的 IIFE。其 4751 行唯一 `window.__demo = {` 锚点之前，研究接口、几何、燃烧、粒子、时钟与随机数绑定均已声明。`bridge.js` 作为明确源码放入此处，安装两个闭包函数；安装本身不读取尚在后文声明的 `EMBED`，不重置、点火、模拟或绘制。

`assemble.mjs` 先验证原文件为 314044 字节，SHA256 为 `e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0`，再验证唯一锚点。输出只有原字节加一个有标记的桥接块，额外验证移除该块可逐字还原原输入。它不改写 URL、相对导入、embed 逻辑、IIFE、初始化顺序或原文件。桥接不得带 HTML script 结束标记。生成页和 `assembly.json` 任一已存在即拒绝覆盖；独占写入失败不自动重跑。

`renderer.generated.html` 被本目录 `.gitignore` 忽略。`assembly.json` 由 root 唯一装配时生成，记录输入、桥接、输出的相对路径、字节数和 SHA256，以及插入位置与标记；不含私有绝对路径。构建代码、桥接和 manifest 可复现装配，不提交整个平台副本。

新 iframe 按 `renderer.generated.html?embed=1&solver=vpm&orbit=0` 正常加载。原脚本先同步完成 embed 暂停和初始化，父页在 iframe load 后才调用桥接。当前 layered research 路径不调用 P4 的相对动态 import。本实现没有 eval、动态函数编译、运行时源码替换、外部页面注入或伪称全局词法访问。

## 两次正文与同一材料

初次材料正文为“我来迟了。”／“你先回去，不必等我。”；换行后为同一份“我来迟了。”／新造的“你再等一会，我就到了。”。三行均原创虚构。两次正文实际由材料点出现在 canvas；HTML 只呈示操作与检查说明。移走旧下行是作者编排，不是火删除请求，也不声称整场完整物理状态移植。

沿用 A39 的 1200×600 源画布、32px 本地 Microsoft YaHei，字体别名仍为 A36Raster；每行独立 1200×96 栅格，anchorY=48、textAlign=left、textBaseline=middle，从 x=y=1 按 stride 2 采样 alpha≥128。每行 anchorX=400；apology 的 sourceY=276，release/request 为 324。采样中心 x+.5/y+.5，id 为 group:y:x。相机 yaw=0、elevation=0、distance=3.4、fov=.85、targetY=1.05；q=2×3.4×tan(.85/2)/600，点 scale=q、opacity=.94、color=[.82,.78,.67]、fuel=1，世界转换与 A39 相同。

apology 只栅格化一次；初次与换行数组直接复用同一组冻结点对象。没有重新栅格化、补点、抽稀、截图字形或人工金色。request 在初始化时单独生成一次，但换行前未放入材料场景。geometry 记录完整 authoredGroups、字体/栅格信息、逐组点数、像素 hash、采样与测量边界、原始点元数据及生成次数。

## 固定参数、动作与停止

`sample.mjs` 显式列出原 RESEARCH_DEFAULTS 全部字段，加上 A39 的既有覆盖：seed=20261031、dt=1/60、elapsed 时钟、legacy 测度、block 粒子策略、9 层×160、graph1400/sample160/feed48、emitter 关闭、spreadFlameHeat/sceneFeed 开启、sceneMax16000。无参数、时长、尺度、容量、燃烧速率或外观搜索。初始化仅调用一次 research.reset；原平台正常载入初始化不计为本页研究 reset。

按钮及阶段不可重复，顺序固定：

1. `first`：ready/frame0 时在源 (480,276)、radius=.12 点火一次，开启既有 spread，逐 RAF 推进180步，停在 first-held/frame180。
2. `handover`：frame180 同步替换下行且零步，绘制后停在 handed/frame180。
3. `later`：在源 (480,324)、radius=.12 点火一次，逐 RAF 推进90步，停在 later-held/frame270。
4. `finish`：不再点火，逐 RAF 推进90步，停在 ended/frame360。

每个 RAF 至多调用一次 research.step(1,1/60)，每次显示绘制至多包含一步；不存在按钮以外的自动模拟，也没有隐藏推进或重置入口。固定点火先记录半径内全部候选点和组（包括已燃点），验证只能直接命中目标组；新下行不得直接命中 apology。命中为零、错组、断言失败、推进中失焦/隐藏/离页均终止，不移动点位或恢复推进。结束断言严格为1reset、2ignite、360steps、1handover、四按钮各一次。失败可能少于预算，不能补足后冒充通过。

原 renderer 自带正常 embed 路径，本页不发送 tick/reset 消息。无人为加速、一次多步、后台补帧或六秒后继续。旧句之后只随正常时钟和间接图传播/火焰热变化。

## 继承桥接的逐值合同

`__a42LocalBridge` 是派生 iframe 中内部制作接口，仅供父页当前按钮处理器调用：`inspect()` 只读，`handover(nextPoints)` 单次。外部检查入口仍只有父页冻结的 `window.__a42.ready` 和 `snapshot()`；没有桥接 step/reset/ignite 方法。

handover 在固定 seed/frame180/time≈3 与完整 A39 参数校验后执行。先核对 id、组、完整 apology 原始元数据与顺序，保存各点 h/fuel/glow/char_/state 和完整 sceneGauss 的 p/cov/sh/c/o；保存旧 burning 的 id 次序与 emitCursor。旧前沿须有效、唯一且 state1，不用额外过滤掩盖异常。

然后仅调用已有 research.setScene 为“apology+request”建场景，按 id 原样恢复 apology 五个材料数组，前沿仅移除 release 并按保留 id 次序映射新索引。emitCursor 数值原样恢复，不 clamp、不取模、不换算；后续既有代码处理其循环。request 保持 state/h/char_/glow=0、fuel1。桥接的整段同步调用不包含 reset、step、ignite、render、await 或随机数抽取。

逐点记录前后完整元数据、完整几何与五个材料值，逐值比较；再断言旧句点数、保留前沿顺序、emitCursor、particleStateHash、粒子对象引用、粒子汇总、时间/frame/seed/vpmTick/vol_t、整个 P、累计计数都不变。legacy areaFeedCredit 前后必须为0。RNG 的内部 mulberry32 状态在闭包内，不探测下一值；保留同一个 srand 闭包引用并严格核对 researchRandomDraws 不变，setScene 路径静态无 RNG 调用。

原 snapshot 的 countersByGroup 只枚举当前几何组；所以另存整个 spreadRegionCounters Map 并逐值核对，保留已移走 release 的历史成本。原 snapshot 不含完整尺度/颜色/opacity/cov/sh，单一 hash 不能替代此处逐点比较。release 点与其移除前沿 id 明确记录。任一断言失败即停止，不回滚、重播或较弱恢复。

## 只读记录、检查分工与艺术判别

`window.__a42.snapshot()` 顶层保留 phase/frame/resetCalls/ignitionCalls/stepCalls/handoverCalls/hash/errors；material 是原 research.snapshot({detail:true}) 完整结果，包含 points/params/counters/particleStateHash。另列完整点分组、geometry、原始/当前材料 hash、粒子 hash、全部组累计计数、前沿、点火坐标/候选/实际命中、handover 逐点记录与所有不变量，以及每步 simulationMs/renderMs/particleCount/hash 和阶段事件成本。

snapshot 不读取实时墙钟、不绘制、不改状态。墙钟成本仅在实际动作发生时记录；冻结期间截图前后全部 snapshot 可直接相等比较。返回对象深复制并冻结，改动返回值不能修改材料。初始化错误或读取错误明确记录，不能当作 ready。

root 在全文读回六个源码后独占一次装配和一次检查：新 inspection-01，不覆盖、不重跑，≤120秒、≤5PNG/8MiB、360步。五图固定为初态、首段3秒、刚换行3秒、后段4.5秒、终态6秒。root 保存源码身份（含生成页与assembly.json）、完整阶段状态/成本、错误/外部请求、截图前后不变证据，并关闭 context/browser/临时 server。本实现者不执行 assemble、浏览器、模拟或截图。

资格只认实际03/04/05旧句字面：继承、行为、仍可读、可见继续变化须分别成立。只有上方火团变化、稳定金色或仅数值变化均不足；无需预设变暗或破损。失败收束当前提案，不延长寻找结局。静态可行和工程投入不要求艺术保留；原平台、A39两份3/6、A40/A41历史及旧评分不变。
