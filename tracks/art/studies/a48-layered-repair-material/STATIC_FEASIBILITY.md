# A48 静态可行性：材料交换成立，呈现边界必须先明确

2026-10-31。仅静态审计；未实现、装配、打开页面、求解、截图、录制、搜索或提交。本文不是运行授权或视觉结果。仅新增本文件，原 demo、A42、A45 和历史文件未改。

已全文读 A47 `CREATOR_CHOICE.md` / `DECISION.md`、A48 `BRIEF.md` 及作者落盘的 `AUTHOR_SPEC.md`。另请一名审阅者只读前三份合同，核对交换边界与几何必要条件，没有再读代码、写文件或执行。此次相关代码只读 `demo/index.html` 一份，约 1,200 行输出（含定位行及少量重复），未读其它实现文件。源码静态身份核对：314044 字节，SHA-256 `e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0`。

## 结论与决策门

现有燃烧数组可承载作者规定的逐格材料，闭包内可以做一次真实、逐值、零步的双向交换。原点火接口也能在固定几何下只命中前片。选择不传播、不生成流体粒子的既有燃烧时钟路线，可静态约束损坏格不越出作者窗口。这是材料状态实验，不能写成完整流体火焰效果验证。

**原 Gaussian `render()` 不能精确落实作者当前图像规格。** 它不是不透明的 4×4 格片渲染：有 EWA Gaussian 核、半透明叠加、炭化改色、独立发光、透视相机及后期。仅把 `charOpa` 改成 1 不够。若“正常 render”被限定为不改该渲染路径、唯一导出它的 WebGL canvas，则应停在这里，当前规格不可直接制作。

有一条需 root 明确接受的普通呈现路线：保留原 demo 的材料求解及其数组，用作者预先规定的 `alpha = 1 - clamp(char, 0, 1)` 直接生成一张新的 720×720 作品画布。纸片几何、线条、底色来自作者规格，透明度来自对应的同一材料数组，h/glow 不进入外观。这个画布是本作的正常呈现和三图原 canvas；它不是对原 Gaussian 渲染结果补洞、贴遮罩或修改导出图。原 Gaussian 图像也不能被冒称为该新画布的生成方式。

本文没有默许这个呈现边界。root 接受并锁定下面的工程常量、只读证据与生命周期后，才有下一步实现资格；不接受则停止，不退回一个近似的 Gaussian 版本来代替作者规格。

## 源码事实及定位

以下行号均指上述固定身份的 `demo/index.html`。

| 边界 | 精确事实 | 源码位置 |
| --- | --- | --- |
| 材料存储 | `sceneBurnState` 内 h、fuel、glow、char_ 为 Float32Array，state 为 Uint8Array；另有有序 `burning` 数组与 `emitCursor` | 1077–1083 |
| 点火 | `igniteAt(wx,wy,wz,r)` 经 `worldToSrc` 后作 3D 球查询，只点燃 state=0 且 fuel>0 的点；没有 group 过滤；公开为 `__demo.ignite` | 1131–1144、4784 |
| 空间查询 | `sceneHash` 是源坐标格哈希，最终仍检验欧氏距离；查询可能按半径重建其加速格 | 1089–1111 及先读的 1101–1125 范围内后续代码 |
| 燃烧时钟 | `stepSpread(dt)` 的入口受 spreadOn 控制；`elapsed` 给所有 burning 项走时钟；消耗 fuel、增加 glow/char_，燃尽才设 state=2、glow=0、char_=1 | 1145–1240 |
| 流体耦合 | spreadFlameHeat 控制火焰加热；spreadSceneFeed 控制场景发射；非发射情况下不应假造或搬移粒子 | 1145–1189、1242–1295 |
| 初始粒子 | `makeLayer` 建空 ps，`resetSim` 重建层并清 embers/cloud 等；`emitSim` 在 emitterOn=false 时立即返回；余烬发射另受 emitterOn 与 embers 控制 | 1457–1474、1497–1518、1608–1616 |
| 正常推进 | `stepAll` 包含 `stepEmbers`、`stepSpread`；`research.step` 在每步增加 simTime 和 researchFrame，并在 finally 恢复 paused | 2584–2610、3362–3370 |
| 场景生成 | `researchSetScene` 存完整 authored 元数据，构造各向同性 covariance 的 sceneGauss；会重建燃烧状态并应用初始 fuel | 3245–3273 |
| reset | `research.reset` 从 RESEARCH_DEFAULTS 合并参数，而不是沿用当前 P；禁 intro/orbit，重置计数并包装 srand 以计 randomDraws | 3343–3355 |
| snapshot | detail=true 才返回逐点材料；hash 中有前沿顺序/cursor，但返回对象没有完整前沿或 cursor 字段；返回的 params、counters、countersByGroup、粒子统计不可丢 | 3282–3334 |
| 原画法 | gatherScene 把 glow、char_ 打包入渲染属性；正常路径为深度桶前向合成 | 899–1006、2809–2898 |
| 原相机 | `updateCam` 使用 m4Perspective，不是作者的固定正视平面投影 | 1377–1396 |
| 公开能力 | `research` 有 setScene/reset/setParams/camera/step/snapshot；render 在 `__demo.render`，ignite 在 `__demo.ignite`，没有 `research.render` 或公开材料 setter | 3341–3373、4751–4784 |
| embed | embed=1 会 paused 并停 intro，但末尾仍启动 loop；loop 即使 paused 仍 render。embed 的 tick/reset 消息也能推进/重置，不能作为本作驱动接口 | 2995–3003、4884–4916 |

取样范围为 469–673、899–1006、1008–1038、1077–1295、1377–1401、1404–1475、1497–1521、1606–1616、2584–2610、2809–2930、2995–3003、3189–3373、4751–4785、4884–4916 的相关片段与定位输出；其中若干相邻范围在实际读取时分开。没有用未读到的 API 承担交换。

## 为什么不能把原炭化当作开口

原 VS_SCENE 的实际公式是：`v_opa = aOpa * (1.0 - uCharOpa * aChar)`。P.charOpa 默认为 0（1447），所以默认炭化不损失覆盖能力。其颜色先由 charDesat、charDim、charSootMix 等混合（637–649），也不是作者的固定纸色。

更关键的是 `v_glow = aGlow`；FS_SCENE 以 `v_color*a + ember` 输出 RGB（652–673）。即使 charOpa=1 且 char=1，alpha 为零，ember 仍可发光。材料还在燃烧时，不能靠透明度参数推断“无火遮挡”。原 `faithful` 只绕过部分后期，仍有 bloom/exposure/dither（469–511）；它不消除上述 ember。

原 Gaussian 的单点覆盖由三倍标准差范围、径向核、投影协方差和低通项决定（515–636）。独立 splat 无法作为作者所说边缘精确接到边界的实心 4×4 方格；相邻透明格还可能由邻点尾部覆盖。原研究 setScene 只收一个 scale 并生成各向同性 cov，没有直接提供“矩形格覆盖”或精确 2px 线的 API。`sceneDepthTest` 是额外的 alpha 阈值深度消融，并不能解决这些问题；正常排序应保持 sceneSorted=true、sceneBackdrop=false、sceneDepthTest=false，不能拿深度消融把问题藏起来。

因此新的普通呈现必须明确绕开这套外观，而非声称调一个参数即符合作者规格。若采用材料格画布，应把每格底色与线段先作为一个共同的表面内容，再只施加一次该格的 alpha；不能先以 alpha 画底色、再以同 alpha 叠线，造成线的覆盖被重复累计。可以在纸片局部坐标生成整张纸面后整体旋转/平移，避免每个旋转格边缘的重复抗锯齿缝。只允许作者规定的普通边缘抗锯齿，不对结果加模糊、补边或裁掉越界材料。

## 可证的材料坐标和命中路线（提案，尚未授权实现）

作者已固定每片 75×100=7500 个材料格，共15000个。按共同的 `(i,j)` 配对，各片材料中心为 `(u,v)=(2+4i,2+4j)`。F 和 B 用不同稳定 id/group，配对由局部格索引决定，不能根据交换前后画布距离重配。

一组可保持作者屏幕几何、又与现有球形 ignite 等价的材料坐标如下：先由 AUTHOR_SPEC 的刚体变换得到画布 `(X,Y)`，再置世界位置为 `[(X-360)/100, (360-Y)/100, z]`，其中 F 的 z=+0.5，B 的 z=-0.5。保持全部 scene transform 为 identity。这是本作普通正视纸片画布的材料坐标约定，不是假称原透视 Gaussian 相机会把两张不同深度的纸投成作者给定尺寸。

F 唯一点火局部 `(8,250)` 对应画布 `(288,330)`，故调用原 ignite 的世界中心为 `(-0.72,0.30,0.5)`，半径0.36。对 F，同片平移/旋转及统一1/100比例保持距离，恰等价于作者的36局部像素圆；B 与中心的 z 差为1，大于0.36，任何 B 点都不可能直接命中。不依赖 group 过滤，也不依赖把后片 fuel 预先改为0。

在不传播条件下，命中中心只能处于局部圆内，所覆盖4×4格的保守范围为 `u∈[0,46]、v∈[212,288]`，包含于 W=`[0,96]×[205,295]`。第一列中心 u=2 中，v=250 的格与点火中心相距6，小于36，故存在接到 u=0 边的命中格。这里是由格几何与球查询公式推得的资格，不是运行得到的缺损图，也没有把 W 当切除遮罩。记录实际命中 id 集合仍是强制条件。

作者已把单片边缘与联合轮廓区分清楚：F 的 W 由 B 承接，B 的对应 W 外露于 F 的左侧。交换仅改变材料所在格，不能改变格位置、格面积或旋转来帮助图像。将来仍可能因为遮挡与缺损形态不够清楚而被作者否决。

## 唯一准备路线及参数边界

以下是支持上述推导的工程候选，root 尚须在实现合同中锁定完整 seed/P 值；不能边跑边选择参数。

- 先一次 `research.setScene` 建立全部15000个原状点，各 fuelInitial=1，材料初态 h/char_/glow=0、state=0。不得预损 B，不留第二套替身缺损。
- 一次 `research.reset(seed, params)`。支持域必须为 solver='vpm'、dimMode='layer'、simLayers=layers；建议最小合法 layers=simLayers=1、ppl=1。设 spreadOn=true、spreadClockMode='elapsed'、spreadMeasureMode='legacy'、spreadBurnT=6。
- 设 spreadRate=0、spreadFlameHeat=false、spreadSceneFeed=false、emitterOn=false、embers=false；spreadOn 不能关，否则时钟也不走。spreadRate=0 是原参数校验允许的值，阻断图加热；前沿仍会被处理并累计真实成本，不能写成“未运行任何计算”。保留合法正 spreadR/spreadIgnR，明确把 ignite 半径作为显式参数传入。
- 按上一节中心与半径唯一调用 `__demo.ignite`，必须返回正命中，且命中集合完全等于事前几何判定的 F 集合；出现 B 或其它点则停。
- 固定360步，每步 dt=1/60。可以调用一次 `research.step(360, 1/60)`，记录 API 调用数1与累计步数360，不能把一次 API 调用记成一步。错误可提前终止，不补完后再重跑；不根据图像择帧。首次素材准备就是唯一准备。

已有 char_ 时钟每次增加 `dt/(burnT*0.85)` 并 clamp 到1；所提6秒准备与作者的 char=1 开口相容。仍须保存实际浮点值，不能把它们强制写为1。fuel 是 Float32Array，不能仅凭6秒/6秒的实数算术断言最终 fuel 恰为0、state一定为2、glow一定为0。新的作者呈现明确不显示 glow，故不需要通过多走几步、清 glow 或清空粒子来制造开口。

此路线使用原 stepAll 和材料时钟，但关闭两个耦合方向和发射。准备后必须实际检查粒子/余烬数量、B完整五元组、F允许区之外的五元组、前沿及 char 值。不能只因参数已设就略掉这些检查。材料数组本体名义大小为15000×(4×4+1)=255000字节；这不包括场景元数据、哈希、前沿、快照、画布、WebGL缓存及原程序初始化成本。120秒整体检查是否足够未运行验证，超时即记录失败，不以第二次尝试补齐。

## 一次零步交换的精确合同

交换须放在原 IIFE 内的本作桥接代码中；可复用 A42 的派生页装配思想，但不能从 iframe 外部假装能访问词法变量，更不能 eval、复制一个伪模型或用 setScene/reset 重建状态。唯一 `window.__demo = {` 锚点4751在闭包内，可在它之前插入限定桥接；原文件逐字保留。未来装配必须重新验证完整源 hash/字节数、锚点唯一性、派生差异清单，并验证桥接自身完整源码。本文没有执行装配或审计未来尚不存在的实现。

设 T 为两片所有对应索引的对换置换，且 T(T(i))=i。每对从交换前的实际值读取后，原地交换 h、fuel、char_、glow、state 的五元组；保留这五个 typed array 本身及长度/类型。逐项检查 `after[F(i,j)]=before[B(i,j)]` 与反向等式，不能只验证总量、分布或 hash。未配对的任何材料点必须逐值不变；本场景若恰只有两片，也应验证配对确实覆盖全部15000点。

前沿按旧顺序逐项映射 `old burning[k] → T(old burning[k])`，不重建、排序、过滤、去重或归一化。保留 burning 数组对象并原位替换元素。`emitCursor` 保留原始实际数值；这个 cursor 是前沿位置，而非场景点 id，不能映射成点索引或对新长度再取模。交换前后检查前沿无非法索引/重复，并与 state=1 的集合一致；若已有不一致则停，不借交换修复。整组对换让前沿长度不变，位置和 cursor 因而保持语义。

其它全局/历史状态不能随材料搬迁：

- 不 reset、不 ignite、不 step；simTime、researchFrame、vpmTick、simSeed、researchRandomDraws 不变，srand 保留同一函数引用且不调用它。
- 保留 layers 及其全部层/粒子值、embers/emberAcc、source/pointer、cloud、vic3、coarse 等其它物理状态；不能因为本路线预期无粒子就只检查数量或顺手清空。
- 全部 P 键值、researchScenePoints 完整 authored 元数据、sceneGauss 的位置/cov/sh/颜色/opacity 及其它实际字段、sceneInfo、sceneHash 的 cell/Map内容与对象不变。纸色、线条、局部格、纸片矩阵和普通画布相机/视图也逐值不变。
- spreadCounters 完整对象、spreadRegionCounters 的完整 Map（包含所有实际键和所有条目字段）、areaFeedCredit 等保持原值。历史成本表示曾在 F 发生的准备，不能改写为 B 的历史。不能只比较 snapshot 已筛出的两个 group 汇总。

应在一次交换函数内完成事前资格检查、五数组和前沿交换、逐值事后核对，再让普通画布读新的 char。核对失败则记录错误并停，不 rollback、第二次交换或补火。整个场景 hash/burnHash 允许改变，因为材料位置确实改变；时间、粒子等摘要应保持相等，但摘要只作辅助证据，不能替代上面的逐值和对象检查。

## 只读证据、可见动作和生命周期

作品只暴露一次“恢复前片”和普通离开方式。准备前原状、准备后、交换后的三张记录均由同一作品原 canvas 直接导出；普通观看从准备后开始。导出或 snapshot 不能推进求解、触发第二次呈示、改变配对或修图。不能开放隐藏 advance/reset/ignite/transfer 接口供检查器绕开按钮。

只读记录至少保留：源身份/派生差异身份、完整参数与seed、作者几何和固定配对、唯一点火的世界/局部坐标及半径、预期/实际命中ids、累计 reset/ignite/step/交换次数、初始/准备后/交换后的完整 `research.snapshot({detail:true})` 原结果、前沿完整索引和id顺序、emitCursor、完整成本 Map、严格不变量比对结果、错误、时间与离开清理状态。原 snapshot 不包含 covariance/颜色/opacity/完整前沿，桥接必须另列这些原始核查证据；不能把 snapshot.hash 当成它已经覆盖的证明。

三图为720×720，合计≤8MiB，无视频。初始/准备后/交换后三图的生成分别计账，不能多导出候选图再挑三张。导出失败亦不产生第四次截图。准备、绘制、读取、PNG完成等待均在单次120秒检查成本内。只读 getter 返回脱离内部对象的值，不能泄露可变引用。

正常 embed 虽 paused，仍有原 render RAF 和可推进的 tick/reset 消息处理。实现必须明确只用 research.step 推进，不发 tick/warm/reset 消息；记录源页面后台渲染及资源成本，不能把它记成不存在。离开应取消宿主页任务、销毁 iframe/其RAF与GL上下文生命周期，释放本作画布缓存并保留已缓存的结束证据。原 embed 没有公开 dispose；不能捏造一个接口。若准备分段或有异步导出，离开后不得继续点火、步进或交换。

## 仍需 root 锁定的项目

1. 是否明确接受作者规则驱动的格片普通画布作为本作原 canvas，承认它是新的呈现层、不是原 Gaussian render。若要求后者，停止制作。
2. 是否采用本文的材料世界坐标/z间隔、零传播无粒子路线及完整配对；固定 seed、完整 P（含未改默认值）、各合法半径/预算值、scene scale/opacity/areaWeight元数据。本文没有暗中将建议变成已批准参数。
3. 将上述严格交换检查具体落实到新桥接，明确只读 API 的返回shape、准备和结束阶段、三图缓存方式、一次按钮闸门、失败和离开处理；不得用后续实现不具备的字段冒称检查已完成。
4. 新画布中纸面/线段共同 alpha 的一次覆盖方式及线位解释应忠实落实 AUTHOR_SPEC；不可另选阈值、形状或颜色。实际同一边缘缺损是否可辨、联合外缘是否显著中断，只能由唯一原画面判断。

以上只支持进入下一次明确决策；不保证艺术关系成立，也没有任何实跑成功可报告。静态审计到此停止。
