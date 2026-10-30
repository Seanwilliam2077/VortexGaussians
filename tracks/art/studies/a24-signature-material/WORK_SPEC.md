# A24 固定材料小样规格

2026-10-31。本文件与四个实现文件在第一次浏览器运行前写定。实现者没有运行浏览器、仿真或字形栅格，也没有看制作后的效果。本案仍不是完整作品；[A23作者否定意见](../a23-fire-material-commitment/COMMITMENT.md)保留，root批准小样的范围见[决定](../a23-fire-material-commitment/DECISION.md)与[BRIEF](BRIEF.md)。

## 对象与可见范围

正文固定为“我们同意将小院的周六晚间开放给放映，并在闭场后共同收拾。”三处署名从左到右为“宁岚、叶青、沈舟”。请求固定为“叶青：下次张贴时，请不要再列我的名字。正文由另两人保留。”三人和事项均为Agent作者选择的虚构内容，不是用户经历、现实当事人授权或已经执行的撤回。

正文与请求是静态HTML；只有三个署名是同一原demo场景中的真实高斯点。不能从正文保持不变推断仿真保护了正文。画面为深底浅字，不模拟真实纸或墨。字符无按时擦除、替换或覆盖遮罩；火与字形由原demo同一渲染过程绘制，外层canvas只复制完整画布，不另改字形像素。

## 固定几何、字形与相机

- 本地字体来源严格为 `local("Microsoft YaHei")`，由 `FontFace("A24Raster", ..., {weight:"400",style:"normal"})`载入。失败即停止，无网络字体或静默替换。Canvas字体字符串为 `400 64px "A24Raster"`，每个两字名字单独在144×80透明栅格中，以白字、center对齐、middle基线、锚点(72,40)绘制。
- x、y采样索引从1开始，步距2像素，只取alpha≥128的点。x/y位置取该像素中心。每像素映射0.008世界单位：x为名字中心加 `(x+.5-72)*.008`，y为`.75+(40-y-.5)*.008`，z=0。三个名字中心x分别为-1.4、0、1.4。
- 所有点材质一致：linear RGB `[.82,.78,.67]`、isotropic Gaussian scale `.0102`、opacity `.94`、fuel=1。每点ID含名字组及栅格y/x，不根据点火或结果改变顺序。名字顺序固定，每名内按行再按列生成。
- 总点数≤8000且每名非空，否则停止，不缩字、不抽稀。字体测量宽度若超过136px也停止。实际点数、每组点数、所用font字符串、测量宽度、采样像素界和完整栅格RGBA的FNV-1a32会在`geometry`记录；尚未运行，不能预填这些值。跨机器字体或栅格器变化不保证点集相同。
- 原画布及外层canvas均为1200×600，响应式页面仅等比显示。相机yaw=0、elevation=0、distance=3.4、fov=.85；原平台目标点仍为(0,1.05,0)。world切片、恒定相机，不使用视角驱动的叙事。场景identity transform，sceneSH=0，box关闭。

## 原平台与一次序列

页面以`demo/index.html?embed=1`读取既有公开接口。初始化调用`research.setScene`一次，再`research.reset(20261031, params)`一次；reset后preview为frame0。`demo.forceSize`、`research.camera`和`demo.render`只确定图像；不通过原demo的播放循环推进。

固定layered VPM：9层、每层160容量、simLayers=9；基础emitter关闭，sceneFeed与flameHeat开启。reset时spreadOn=false；点火一次后设true。legacy时钟、block粒子规则、legacy点测度；其余传播、燃烧和着色参数使用`RESEARCH_DEFAULTS`，包括spreadFrontierCap=1400、sampleCap=160、feedCap=48、burnT=6、charDesat=.85、charDim=.12、charOpa=0。没有修改原demo默认值或借用elapsed时钟。全部实际参数随snapshot记录。

唯一初始点火中心为(0,.75,0)，半径.40；调用原`demo.ignite`后，实际点火数若不是1..1400内的整数，立即停止，不移动点火或改变预算。点火后没有自动step。

正常UI路径为：初态 → `#ignite` → `#advance`三次。每段恰好120个`research.step(1,1/60)`，每个RAF最多一步，不追赶墙钟、不批量跳步。各段在frame120、240、360暂停端点；总360步/6模拟秒。端点可无限停留，不自动开始下一段。`#pause`只在段内暂停/继续，保留本段目标；`#leave`提前停止推进并保留当前图像，不清除材料。完成后没有重置、重燃或额外推进按钮。

## 只读检查与图像解释

`window.__a24`只含`ready` Promise与`snapshot()`；没有隐藏推进接口。snapshot返回独立副本，含phase、frame、simSeconds、段目标/完成数、resetCalls、ignitionCalls、initialLit、geometry、事件和错误。phase为loading/ready/ignited/running/paused/held/ended/left/error。预期正常端点是ready0、ignited0、held120、held240、ended360。

每次snapshot都从公开`research.snapshot({detail:true})`读取当前点状态，然后只返回摘要，不返回巨量逐点数组：`groups`按ning-lan/ye-qing/shen-zhou分组，含heat/fuel/fuelInitial/char/glow的sum/mean/min/max/nonzeroCount，以及state0/1/2计数；`total`同样汇总全组；`hash`和`material`保留原平台摘要、参数、计数器与状态身份。字形是否可读仍须看原图，不能由char或heat的非零推出。UI表格显示最近停留点；运行中明确标为旧停留点摘要，段内暂停和端点均刷新。

没有模型几何删除，没有宣告署名撤回成功，也不将火下的暂时遮挡等同于不可逆损毁。检验仅是材料着色是否参与署名可见变化、邻组是否仍能辨认，以及亮火与暗变的关系是否可见。正文未参与模拟，社会后果、持续指认和真人体验均未检验。

root另按BRIEF执行最多一次≤120秒正常UI检查，保存0/点火后/2/4/6秒及结束后窄屏图，总量≤8图/12MiB。不录像、不调效果、不因阴性结果重跑。若执行故障，先记录，再决定是否值得修复。本次实现交付不表示这些检查已经通过。
