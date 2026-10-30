# A38《末班之后》动作与材料规格

2026-10-31，首次运行前固定。依本目录BRIEF与A35原文制作完整六行。A37只建立桌面两行初态的制作条件，本文件不预报全文阅读、互动效果或艺术评分。实现仅写index.html、work.css、work.mjs与本文件，旧版本和原demo不改。

## 字面

六行依次为：

> 末班车九点十二分开走。  
> 请把长凳推到门边，留出一人睡觉的地方。  
> 时刻表不要摘，明早第一班仍是六点四十。  
> 若有人问今晚还能不能走，先把今晚那一行念完，再把门打开。  
> 暖水瓶里剩的水不够两杯，留给最后进来的人。  
> 我把钥匙压在纸下；你离开时，把这张纸放回钥匙上。

全文为原创虚构交接条。画布正文全部是原平台高斯材料字，没有静态替代正文、擦字遮罩或受热字幕。标题、虚构说明、操作提示和可折叠方法在画布之外。

源画布与外层canvas均1200×600。字体严格为local Microsoft YaHei，沿用A36Raster别名、400 32px；每行1200×96透明栅格，left/middle锚(280,48)，白字，固定stride2、alpha≥128、像素中心、行内y/x顺序。六行按line1..line6排列，源坐标middle y为204/252/300/348/396/444，x均280。第三、第四行的位置构造与A37相同。

每源像素世界尺度 `q=2*3.4*tan(.85/2)/600`。样本源坐标 `sx=x+.5`，`sy=line.sourceY+y+.5-48`；世界坐标为 `[(sx-600)*q,1.05+(300-sy)*q,0]`。scale=q、RGB[.82,.78,.67]、opacity=.94、fuel1，与A37相同。相机yaw0/elevation0/distance3.4/fov.85、目标(0,1.05,0)、world切片与identity场景不改。

makeScene及字形metadata沿用A37，只增加四行并将预定总点资格与sceneMax改为16000。字体、字宽、墨迹界、各行非空和子组非空资格失败即停止，不替换、抽稀、缩字或移动布局。每行保存完整文字、点数、测量界、采样界、整栅格RGBA FNV-1a32，另记全部域外点数。每点唯一primary group为所属行；保留第三行[3,6)字符列的“不要摘”子组，子组不重复计入total。

桌面单列可呈示1200 CSS px；边框使用outline，不缩窄canvas内容。窄屏只等比显示，不据此承诺全文或手机逐字可读。长句部分点位于流体x∈[-1,1]之外；完整字面不是均匀热动力学的纸。

## 按住与停留

初始化setScene一次、research.reset一次，seed20261031，ready后不自动推进。没有预设点火位置或吸附规则。画布内主指针左键/触摸按下建立hold，以实际canvas bounds线性换算源坐标，再按同一q换算世界坐标；不裁限或修改合法画布内的触点。

pointerdown立即以radius=.12点火一次并render当前状态，不推进步数。随后每个RAF至多按当前触点点火一次，再research.step(1,1/60)一次并render；没有墙钟追赶、批量step或按move事件数推进。零命中允许继续，已燃点不会因再次点火而重置。既有火按原模型传播，不随触点搬走。

按住不移动也推进。pointermove只更新当前触点并记录事件；捕获期间仍检查bounds，越界即冻结。pointerup、pointercancel、pointerleave、捕获意外丢失、窗口blur、document hidden和pagehide都终止hold、取消RAF并释放捕获。普通移动不推进。读多久都不增加模拟时间；再次按住从当前frame继续。

每遍累计最多360步。第360步render后自动终止hold并进入ended，保留整页字面，没有再进入运行的入口。无论何时松开，都记录实际frame，不把任意松开伪称120或240。

平台继续使用A37的9层×160、legacy clock/block/legacy measure、frontier1400/sample160/feed48；基础emitter关闭，sceneFeed/flameHeat开启。每遍reset时spreadOn=false，首次点火后设true；释放时不改材料参数，通过不再step冻结。其余RESEARCH_DEFAULTS包括着色、曝光和光晕不改。

## 结束与另一遍

`#leave`取消推进，保留当前材料状态，将画布呈示隐藏并进入left，显示明确结束提示。它不清除模型、宣告烧尽、交接完成或旧文件丢失。

left状态的`#restart`写明“从原文开始另一遍”。它先归档当前遍的frame/hash/计数/行状态，再对同一全文调用research.reset，恢复frame0与全部初始燃料，进入ready。初始化只setScene一次，重开不重新抽取字形。resetCalls、ignitionCalls、totalStepCalls、totalIgnitionHits、holds和events均跨重开累计保留；run/frame/本遍计数才重设。错误状态没有重试按钮。

| phase | 含义 |
| --- | --- |
| loading | 初次准备字体与原平台 |
| ready | 本遍初态，可先读 |
| running | 一个有效hold推进中 |
| held | 提前释放或其他冻结，保留当前frame |
| ended | 到达360步，画布继续可见 |
| left | 观者结束，画布隐藏，材料仍在 |
| error | 初始化、数值或输入错误，停止并保留错误记录 |

## 只读记录

`window.__a38`是冻结且不可重赋值/配置的对象，只公开ready Promise和snapshot()。读取不推进、不render，返回独立副本，不暴露可写材料或隐藏步进入口。

- phase/frame/time/simSeconds、run、running、activeHold、累计resetCalls/ignitionCalls/totalStepCalls/totalIgnitionHits，以及本遍点火调用/命中。
- geometry完整沿用字形来源记录；groups.line1..line6及不重复total含点数、heat/fuel/fuelInitial/char/glow摘要和state0/1/2计数；subgroups只作重叠参照。
- 每个hold保存起止frame/墙钟、pointerId/type、stopReason，以及实际pointerdown/move/up/cancel/leave/捕获事件的frame和坐标。releaseObserved表示是否收到释放事件，自动到限或越界冻结不冒充已收到pointerup。停止原因另在events保留。
- hold.ignitions逐次记录累计call序号、pointerdown或before-step触发、源/世界触点、半径、newlyLit；推进对应stepCall、frameBefore/frameAfter。即使点火或推进失败，也不抹掉已经发出的调用。
- material保留实际hash/particleStateHash、params、scene、particles、原计数器与按行计数。counters为当前遍；completedRuns保存旧遍。cumulativeBudgets累加frontierDeferred/frontierProcessed/clockProcessed/clockFuelConsumed/flameSampleCapHits/sceneFeedAttempts/sceneFeedCapacityBlocked，重开不擦掉旧预算使用。
- canvasVisible、实际sourceCanvasSize、errors/events及snapshotError。数值读取失败时snapshot仍返回已有输入和错误状态，不伪造材料摘要。

frontierDeferred表示点×步延期，不是唯一受影响点数；state2只表示代码fuel≤0，不恢复逐点延期史或称正常燃尽。数字不代替可读性或作品关系。折叠统计在停留时刷新；运行中明确显示最近停留点，snapshot仍读取真实当前状态。

## 运行前边界与检查附录

实现者仅制作四文件与允许的node --check静态语法核验，没有运行字体栅格、浏览器、仿真或截图，也没有外部检索、依赖安装、提交或额外任务。作品需仓库同源HTTP服务；不承诺file://运行。

root独占的一次输入路径与截图预算以已冻结的[INSPECTION_PROTOCOL](INSPECTION_PROTOCOL.md)为准。本实现不复制或改变协议，也不在代码中内置该轨迹。一次运行结果、成本和图像由root另行保存，不能用工程通过替代观看或评分。
