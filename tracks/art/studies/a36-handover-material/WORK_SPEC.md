# A36《末班之后》两行材料规格

2026-10-31，首次执行前固定。依本目录 BRIEF，仅制作第三、第四行的材料核查，不制作全文、拖拽或额外点火。四个实现文件独立于旧作品与 demo；本文件不预报可读性、邻行变化、火形或艺术效果。

## 固定字面与材料

第三行：“时刻表不要摘，明早第一班仍是六点四十。”

第四行：“若有人问今晚还能不能走，先把今晚那一行念完，再把门打开。”

文字为原创虚构交接条摘录。可见正文全部是原平台高斯材料字，不叠加替代正文。标题、虚构声明、控制和材料说明在画布外。

- 字体严格载入 `local("Microsoft YaHei")`，别名 A36Raster，`400 32px "A36Raster"`。字体不可用即停止，不替换、不联网。
- 每行独立1200×96透明栅格，白字、left对齐、middle基线，锚点(280,48)。不使用fillText的maxWidth。宽度与实际墨迹bounds超出栅格即停止。
- 第三行映射到源画布锚点(280,300)，第四行到(280,348)。两行顺序固定；每行从y=1/x=1开始、步距2，按行再按列采样alpha≥128的像素，取像素中心。ID为 `line3:y:x` 或 `line4:y:x`。
- 每源像素世界尺度 `q=2*3.4*tan(.85/2)/600`。栅格样本对应源坐标 `sx=x+.5`，`sy=line.sourceY+y+.5-48`，世界坐标 `[(sx-600)*q, 1.05+(300-sy)*q, 0]`。保留yaw0/elevation0/distance3.4/fov.85、目标(0,1.05,0)，world切片、identity transform。
- 32px字号与48px行距对应1200×600源画布的名义像素尺寸；墨迹bounds依字体与采样而定。外层canvas完整复制同尺寸源画布，桌面可显示1200 CSS px宽；窄屏等比缩小，不保证32 CSS px或逐字可读。
- 高斯scale=.0102，linear RGB[.82,.78,.67]，opacity=.94，fuel=1。保留A24每点足迹，接受32px字形可能粘连；不运行后缩scale、减少模糊或改遮罩。
- 每行非空，总点≤8000，目标子组非空，否则停止，不抽稀。geometry记录字体测量、实际采样界、整栅格RGBA FNV-1a32、点数及域外点数，不预填运行结果。

“不要摘”取第三行零起算字符索引[3,6)。固定用同字体测量索引3/6之前的前缀宽度，得到从x280起的列边界；样本中心落在该半开区间者列入子组。它是空间列归属，不另造或重复添加点。平台primary group始终为line3/line4，子组ID为do-not-remove；两行摘要完整保留，total直接汇总全部唯一原点，不将子组再相加。

## 点火与一次六秒序列

源画布固定点(424,300)，即 `[(424-600)*q,1.05,0]`，约x=-.90275，半径.12。只调用一次demo.ignite；返回整数1..1400且与点状态计数相符才可推进。实际初始点火总数、两行数、不要摘子组数均记录，不承诺仅命中一个字或整段文字。

初始化research.setScene一次，research.reset一次，seed20261031。9层×160容量，simLayers9，layered VPM；基础emitter关闭，sceneFeed与flameHeat开启。reset时spreadOn=false，点火后才true；legacy clock、block粒子规则、legacy measure，frontier1400/sample160/feed48。其余沿用RESEARCH_DEFAULTS，包括burnT6和A24的charDesat.85/charDim.12/charOpa0，实际params随snapshot保留。

原流体横向域为x∈[-1,1]；点火中心在其内，长句部分材料点在其外。字形仍有图邻接，但不声称整页具有均匀或对称的流体反馈，不根据结果改左边距。

控制沿用A24：ready → 点火但不推进 → 三次120步段。每步research.step(1,1/60)，每RAF至多一步，无墙钟追赶或批量推进，端点frame120/240/360停留。段内暂停/继续保留段目标。停止在这里取消RAF、保留画面与状态；不清除材料，不宣告纸已毁掉或交接完成。无重置、重燃或额外推进按钮。

## 状态与计数

`window.__a36`冻结、不可重赋值，只公开ready Promise及snapshot()。snapshot读取research.snapshot({detail:true})并返回独立摘要；不推进、不渲染、不暴露逐点数组或可写状态。

- `phase/frame/simSeconds/segmentEnd/segmentsCompleted`及resetCalls、ignitionCalls、initialLit、geometry、events、errors、endedBecause。
- `groups.line3/line4`与`subgroups["do-not-remove"]`：count，heat/fuel/fuelInitial/char/glow的sum/mean/min/max/nonzeroCount，以及unburned(state0)/burning(state1)/fuelDepleted(state2)/other计数。total汇总唯一全集。
- `initialLitByGroup`及`initialLitSubgroups`记录尚未推进时的实际点火状态；子组标记parentGroup与overlapsParent。
- `counters`及material.counters为实际累计计数，material.countersByGroup保留原平台分组计数；`endpointRecords`在ready0、ignited0、held120、held240、ended360记录frontierDeferred/clockProcessed及相对上一端点的增量。段内暂停只刷新停留摘要，不改端点增量基准。
- `hash/material`保留原状态身份、scene、particles、params和随机抽样计数。`sourceCanvasSize`记录实际源尺寸，绘制前检查必须1200×600。

legacy模式只对前沿前1400项推进传播与燃烧时钟；超额点可延期，frontierDeferred累计的是点×步次数，不是唯一点数。state2来自代码fuel≤0，并会被移出前沿，不称为“永不退休”。capDelayObserved表示出现过延期；不逐点恢复延期史，也不声称某点正常耗尽。六秒只是固定推进上限，不保证耗尽或不可读。

正常UI选择器为#ignite/#advance/#pause/#leave；画面#view、源iframe#source、错误#error、状态#phase-text/#sim-time。统计默认折在details，运行中表格明确显示最近停留点，暂停和端点刷新。

## 核验范围

实现者只读冻结文档和既有实现，写上述四文件，允许静态语法核验。没有运行字体栅格、浏览器、仿真或截图，也没有安装、外检或提交。本小样需通过仓库本地HTTP服务读取同源iframe；不承诺file://可运行。root独占一次限定UI检查，结果另行保留；静态实现不代表材料或艺术判断通过。
