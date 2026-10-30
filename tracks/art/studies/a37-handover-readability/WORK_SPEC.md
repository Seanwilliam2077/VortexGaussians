# A37《末班之后》初态阅读规格

2026-10-31，首次执行前固定。依本目录冻结BRIEF，承接A36作者选择，仅检查初态字面。实现只写index.html、sample.mjs和本文件；页面直接引用A36 sample.css。A36源码、图像与实际结果不改。

唯一材料差异是Gaussian scale：从A36的.0102改为 `WORLD_PER_PIXEL = 2*3.4*tan(.85/2)/600`，约.0051292757。使用作者选择的1源像素投影sigma，不使用先前静态分析中的.8px例，也不比较多值。shader自身低通、离轴投影及后期仍沿原平台，不能把该参数称作最终笔画宽度或保证清晰的1像素字。

## 保留的字形与平台

两行文字、字体来源与内部别名`A36Raster`、`400 32px`、1200×96各行栅格、left/middle锚点(280,48)、映射源锚点(280,300)/(280,348)、stride2、alpha≥128、像素中心与生成顺序，完整沿用A36的makeScene。点ID仍为`line3:y:x`/`line4:y:x`，位置公式相同；因此在同一本地字体与栅格器下沿用同一点身份和位置构造，仅点scale不同。运行前不预填实际点数或栅格哈希，也不冒称已完成跨版本运行比对。

颜色[.82,.78,.67]、opacity=.94、fuel1、z0、相机yaw0/elevation0/distance3.4/fov.85、目标(0,1.05,0)、scene identity及全部PARAMS与A36相同。字体、字宽、墨迹界、每行非空、子组非空及总点≤8000资格保持；失败即停止，不改字、不抽稀、不重试。

“不要摘”继续由第三行字符索引[3,6)之前的同字体前缀宽度确定列边界；子组是line3的子集，不另添点、不重复计入total。geometry保留每行RGBA FNV-1a32、实际bounds、字体、点数、目标子组和域外点数，供与旧记录对照。

源画布和外层canvas均1200×600。桌面沿用A36单列1200 CSS px呈示，不加画布内正文、遮罩、对比修正或光晕设置。平台仍为9层×160、seed20261031、legacy clock/block/legacy measure及frontier1400/sample160/feed48；emitter关闭，spreadOn=false，其余RESEARCH_DEFAULTS不改。

## 只有初始化

research.setScene一次，research.reset一次，forceSize/camera确定画面，render初态并完整复制源canvas。页面没有点火、推进、拖拽、暂停或重置按钮，脚本没有demo.ignite、research.step、setParams或RAF推进路径。

初始化读取真实snapshot并核对frame0、time0、zero burning、全部state0、每点fuel=fuelInitial及fuel loss总和0；失败显示错误并reject ready。正常ready后无限停留，不推进模拟。20秒初始化超时即记录失败，不自动重试。

`window.__a37`为不可重赋值、不可配置的冻结对象，仅有ready Promise和snapshot()。读取只生成独立摘要，不渲染、不推进，不暴露逐点数组或写入口。记录：

- phase、实际frame/simSeconds、resetCalls/ignitionCalls/stepCalls、geometry、errors/events。
- groups.line3/line4、subgroups["do-not-remove"]及不重复total；heat/fuel/fuelInitial/char/glow摘要与state计数。
- initialState中的frameZero/timeZero/zeroBurning/allUnburned、fuelLoss、unchangedFuelCount，均从原点状态计算。
- material完整实际params、scene、particles、counters/countersByGroup、hash/particleStateHash及randomDraws；sourceCanvasSize记录实际源尺寸。
- materialDifference单独记录scale前值/当前值及不变的点构造。原平台状态hash不是scale变化的充分证明，应同时检查geometry.raster.gaussianScale。

主要检查节点为#view、#source、#loading、#error、#phase-text、#time-readout；统计在默认折叠details中。字体载入与同源iframe需要仓库本地HTTP服务，不承诺file://可用。

## 实际核验边界

实现者只读冻结文档、复制和精简A36代码，并可执行node --check静态语法检查。没有运行字体栅格、浏览器、模拟、截图或外部检索。root将独占一次初态检查，限一张原始PNG及JSON；本规格不预报阅读结果，不以初始化通过替代制作或艺术判断。
