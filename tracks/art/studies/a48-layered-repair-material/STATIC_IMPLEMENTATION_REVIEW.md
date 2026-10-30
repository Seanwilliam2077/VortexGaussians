# A48 独立静态实现审阅

2026-10-31。审阅者仅作代码与合同核对，不作艺术评分。本次只新增本文件，没有修改被审实现、原 demo 或历史文件。没有装配、启动服务或浏览器、执行页面/数值、生成图像、运行语法或测试程序、检索外部资料或提交。

## 结论

发现一处应在唯一执行前修正的合同缺口：检查器的截止路径可能丢弃已经存在的阶段材料与原图证据。正常成功路径中的闭包桥接、固定准备、对应格交换、二维呈现和三图限制，未发现具体执行阻断或偏离已锁定规格的实现。此结论只来自静态阅读，不代表运行通过、作者保留或艺术关系成立。

## 实质问题

**[P2] 110 秒截止先销毁页面，未保存已有阶段证据。** `inspect.mjs:38–40` 在 soft deadline 设置 `expired=true` 后直接调用 `closeResources()`，首先关闭 context；`inspect.mjs:167` 又以 `!expired` 为条件，跳过异常路径的 `read()` 和 `exportCachedImages()`。`lastSnapshot` 只由 `read()` 赋值（48），正常流程首次读取在等待 prepared 结束以后（146），最终写出 snapshot 又要求该变量存在（181）。因此若截止时页面仍在自动准备，页面已经缓存的 initial/ignited 材料和 initial PNG 会随着 context 关闭而丢失，结果中甚至没有这些已发生操作的调用数；若截止发生在恢复过程，则最后缓存可能仍是 prepared，已经发生的交换与第三图情况也无法得到保留。

这违反 `IMPLEMENTATION_DECISION.md` 的“超时或任何资格失败记录已发生动作与可得材料，关闭资源，不补跑”。问题是证据回收顺序，不是要求超时后继续点火、步进、生成图或重跑。可在截止关闭前预留有严格短限时的只读取证并保存最近已得记录，或在正常准备期间保存阶段 checkpoint；无论采取哪种方式，都应保留120秒总限额并确保最终关闭。不能把“页面暂时不可响应”当作无界等待理由。

本次读到的 `closeResources()` 已先等待已有 closing，再重新遍历当前 context/browser/server，跳过已关闭资源；没有把此前迟到 handle 的旧问题计入本次问题。当前指出的是独立的截止证据缺口。

## 已核对且未发现实质偏差的部分

- `assemble.mjs` 检查固定源字节数/hash、唯一 `window.__demo = {` 锚点和纯插入重构；桥接安装位置处于原 IIFE 内，所引用绑定存在，实际运行延后到源 load 完成后的单次握手。没有 eval 或替代燃烧器。
- 原 reset 从 `RESEARCH_DEFAULTS` 合并，覆盖与实施决定一致；源点顺序、id、F/B局部配对、世界映射和元数据一致。唯一原 ignite 的球命中集合被逐点核对；一次 step API 请求360个1/60积分步。原时钟允许 char 到1而 fuel/state/glow保留实际浮点结果。
- 原 sceneHash 格幅为0.14，查询半径0.36与0.11均未触及原 `hashQuery` 的四倍/四分之一重建条件；因此当前固定几何校验不会仅因这两个合法查询误报加速格漂移。
- 五材料数组原地逐对交换；burning 原数组按原顺序映射，cursor不重新计算。交换前后以逐值和对象引用核对材料、几何、参数、完整历史counter/Map、物理值与RNG引用/计数。完整世界hash在交换后允许变化；检查器只要求独立粒子hash不变，没有把材料迁移误当成异常。
- 新画布将纸色或线色先选入同一局部RGBA像素，再只赋一次由char得到的alpha。F/B位置、屏幕逆时针12度旋转、线位/宽度/范围、75×100格及4px幅、两次纸面drawImage和不透明背景与规格一致。W只用于资格核对，没有作为切除遮罩；交换后的同一char值通过同一(i,j)呈现。
- initial/prepared/swapped各只绘制并toBlob一次；ignited仅记材料。PNG等待前后核对材料与物理状态，图像接口只返已缓存原图；inspect返回脱离内部对象的记录。读取成本自记不会被误报为材料修改。
- 检查器通过真实 `#restore` 点击执行唯一动作，未调用隐藏材料入口；正常结束通过 `#leave` 点击，并检查iframe移除、局部画布释放与结束证据保留。原 embed 在2994直接安排下一RAF后返回，不自行render或step；宿主没有发tick/reset消息。
- 检查器逐项核对四阶段原snapshot与源序五数组、对应交换、前沿/cursor、物理和完整成本；直接保存既有三PNG，检查原尺寸、字节与hash，总量不超过8MiB。正常路径关闭一个context、browser和临时随机端口server，已有inspection-01拒绝重用。唯一剩余实质缺口是上面的截止证据回收。

## 真实读取范围

全文读取：`IMPLEMENTATION_DECISION.md`、`AUTHOR_SPEC.md`、`STATIC_FEASIBILITY.md`；八个实现/说明文件 `bridge.js`、`work.mjs`、`assemble.mjs`、`index.html`、`work.css`、`.gitignore`、`inspect.mjs`、`WORK_SPEC.md`；检查器实际导入的 `research/lib/runtime.mjs`。

原 `demo/index.html` 仅作定位及必要片段阅读，包括IIFE/WebGL初始化、sceneBurnState与hash/ignite/时钟（1008–1295）、相机/参数/reset/层初始化、发射关闭分支、VPM池及空粒子准备、stepAll（2574–2615）、loop入口（2990–3010）、相关UI初始化、research场景/快照/reset/step（3189–3374）、公开入口（4748–4795）和embed/末尾初始化（4880–4919）。另用rg定位所引用词法绑定；没有全文审计其它求解器或原渲染器。

原源身份采用实施决定锁定的314044字节与SHA-256 `e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0` 作为审阅前提；本审阅没有自行运行文件hash、装配校验或检查器。审阅到此停改，问题交root处理，不追加执行预算或艺术判断。
