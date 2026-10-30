# A48 实现说明

本实现按 `IMPLEMENTATION_DECISION.md`、`AUTHOR_SPEC.md` 制作。当前仅代码与静态语法检查，未装配、启动页面、求解或产生图像。原 demo 和所有历史文件未改；不预认材料资格、作者保留或论文贡献。

## 文件与普通流程

- `assemble.mjs` 只读固定314044字节、SHA-256 `e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0` 的原 demo，在唯一 `window.__demo = {` 前纯插入 `bridge.js`。删除插入块必须逐字还原原文件。生成的 `renderer.generated.html` 和 `assembly.json` 不入 Git，均独占创建，已有文件则拒绝覆盖。
- `index.html` / `work.css` 只提供720方画布、准备遮盖、一次“恢复前片”和离开。`work.mjs` 读取装配manifest，按正常 `?embed=1&orbit=0` 载入同源派生页。
- 桥接通过源 load 时的一次临时私有握手连接宿主模块；不创建 window bridge 或公开材料控制接口。安装桥接时不求解。原 embed 只有空转 RAF，入口早退，不自动 render/step；没有发 tick/reset 消息。源初始化与该 RAF 生命周期成本仍存在。
- 自动流程：一次 setScene → 一次 research.reset → 原状材料记录/绘制/PNG及不变量检查 → 一次原 ignite → 命中材料记录 → 一次 research.step(360,1/60) → 准备后记录/绘制/PNG及不变量检查 → 才揭开遮盖和启用按钮。
- 真按钮的一次尝试同步交换材料，核对后绘制/导出第三图，进入 ended。无动画、第二次点火、求解、交换、准备或重试。异常进入 error，现有证据保留；离开进入 left 并清理资源。

## 固定材料与呈现

源点为F行优先7500点、B行优先7500点，id `F:i:j` / `B:i:j`，局部中心 `(2+4i,2+4j)`。作者屏幕坐标映成 `[(X−360)/100,(360−Y)/100,z]`，F z=.5、B z=−.5。元数据 fuel=opacity=1、scale=.02、color=[228/255,221/255,204/255]、areaWeight=.0016，group=F/B。

seed=20261031。`bridge.js` 的 overrides 完整列出实施决定的覆盖，reset从固定源 RESEARCH_DEFAULTS 合并；初始化和各次记录逐键核对全部P。唯一点火 `__demo.ignite(-.72,.30,.5,.36)` 的实际命中必须恰等于事前球查询集合且只含F。spreadRate=0，elapsed、burnT=6，两个耦合方向和emitter/embers均关闭。这是固定命中格的既有材料时钟，不是传播形状或流体图像。

画布是新普通二维材料呈现，不是原Gaussian输出。两张300×400 RGBA纸面按像素生成，每像素选纸色或线色，再赋一次 `round(255*(1-clamp(char_,0,1)))`。线中心34/162/234、宽2，v∈[20,380)。B整体旋转−12°后平移到(300,390)，F放在(280,80)；每片每次只drawImage一次。主画布先填#1D2320。没有按命中圆或W绘制缺口，W只用于材料资格检查；实际透明度只来自原char_数组。8位alpha量化及普通Canvas变换抗锯齿如实保留。

名义RGBA缓存：主画布2073600字节，两张纸面Canvas960000字节、两份ImageData960000字节，总3993600字节；不含源WebGL初始化、JS场景对象/快照、PNG/base64、浏览器及驱动开销。五原材料typed array的名义数据量为255000字节。所有阶段存原浮点材料，不能用6秒算术将fuel/state/glow强制燃尽。

## 交换与证据

五数组 h/fuel/glow/char_/state 在原对象内对换 i 与 i+7500；原 burning 数组逐位置应用同一置换，顺序不变，emitCursor不赋新值。逐对比较交换前后每个原值。未调用setScene、reset、ignite、step、render或RNG。检查typed arrays、原数组/嵌套对象、几何/元数据/hash格、srand函数引用、全部P、独立物理值、完整历史counter/Map及areaFeedCredit。失败不回滚。

每阶段保存原 `research.snapshot({detail:true})` 完整结果和按源顺序的五数组；前沿索引/id顺序和cursor另存。完整几何及源元数据只存一次，阶段用 `geometryRef` 指向它，内部每次仍逐值/对象核对。独立物理状态用完整值比较后去重并由 `physicalRef` 引用，包含层/粒子、余烬、source/pointer、coarse、cloud/vic3、VPM缓冲、相机、时间、RNG计数等。typed array记为 `{type,values}`，Map记为 `{type:'Map',entries}`；完整成本Map保留全部条目和字段，没有只留下F/B汇总或hash。

四个材料阶段为initial、ignited、prepared、swapped，只有initial/prepared/swapped各绘制和导出一次。每次异步PNG前后核对材料、前沿、物理、counter、几何及原snapshot保持相同。准备检查B及F未命中点五元组不变、char变化格完全在W中且接到左边缘、无粒子/余烬/cloud；独立检查器再比较逐对交换与历史成本。图像是否足以读出关系仍由作者判断。

## 只读接口

`window.__a48` 是不可替换的冻结对象，只含两个函数。所有返回值脱离内部引用。

`inspect()` 返回：

```
{
  version, phase, phaseBeforeLeave?, artifactsReady, errors,
  identity: assemblyManifest,
  source: {
    calls: {setScene,reset,ignite,stepAPI,steps,restore}, seed, dt,
    geometry: {id:'geometry-0',value:{authored,gaussians,sceneInfo,hashGrid},pairing,canvas},
    physicalStates: {'physical-0':fullState, ...},
    stages: {
      initial, ignited, prepared, swapped
      // each: {name,geometryRef,geometryEqual,physicalRef,material,
      //        arrays:{h,fuel,glow,char_,state},frontier:{indices,ids,emitCursor},
      //        counters,groups:{type:'Map',entries},areaFeedCredit}
    },
    ignition, preparation, exchange, pngChecks, timings, errors, failure?
  },
  draws, pngAttempts, images:[PNG metadata only], costs, cleanup
}
```

`inspect({summary:true})` 只返回version/phase/artifactsReady/errors/calls/imageCount/cleanup，供检查器等待阶段。正常phase为loading→preparing→prepared→restoring→ended；异常error，离开left。ended且artifactsReady=true表示三图及最后的材料不变量核对完成。

`images()` 仅返回已经缓存的：

```
{ images:[{file,stage,width,height,bytes,sha256,completedAtMs,dataURL}],
  totalBytes, complete, sourceIdentity }
```

文件固定为`1-initial.png`、`2-prepared.png`、`3-swapped.png`。接口不绘图、不编码、不求解，也不提供隐蔽控制。两接口仅自记读取次数与CPU复制耗时到costs.inspection/imageReads；因此不能宣称整个record逐字不变。材料、物理、几何、操作计数和已存图证据在读取前后不变；harness明确只比较这些部分。

## 限额、清理与唯一检查

三张720×720原canvas PNG合计≤8MiB，无视频或截图替代。每次PNG只调一次toBlob，编码最多等15秒，失败不换方式或重试。普通准备最多110秒等待；同步原step仍是一段固定360步，不能按效果缩短/续跑。root的整体检查预算包括初始化、求解、核对、绘制、编码、读回和关闭。单项耗时不是GPU基准。

离开/error/pagehide停止宿主待办、取消PNG等待、移除iframe及其空转RAF生命周期、释放两纸面Canvas/ImageData与主画布内存。结束记录和已编码PNG保留。源没有公开dispose，不捏造该接口。页面自身没有RAF循环或视频/stream；不把原iframe的初始化和RAF成本记为零。

`inspect.mjs` 默认不执行页面。仅root审计后允许一次装配及一次`node inspect.mjs --execute`。检查器独占创建inspection-01，用已有runtime建立随机本地端口（不使用常驻8137）、一个browser/context；只普通加载、点击#restore一次、读记录/已存图、点击#leave。110秒停止后续harness动作，关闭前以最多2秒总读取预算尝试一次只读inspect和已有images；若已有普通读取/导出进行中，则加入同一Promise，不重复导出。期限后忽略迟到响应；页面无响应、接口错误或无页面时，在partialEvidence中明确记下未取得原因，不称证据完整。随后关闭全部资源，120秒硬截止不变，无新图、动作、重新加载或补跑。执行前后核原源码、派生页及实现文件身份，并逐字重构纯插入关系。

检查器保存三图、一个包含完整阶段证据的snapshot.json和精简result.json；不把完整源几何/材料在多个结果文件中重复抄写。若失败，只保存已有材料/图像，不补造缺少阶段。成功取回的部分snapshot与已发生调用先在关闭前落盘；120秒硬截止也走同一独占写入函数保存最近已取得的snapshot/调用，避免soft与finally并发导出或互相覆盖结果。没有成功读取时只能保留已有harness记录和缺失原因。关闭context、browser、临时server均记录。读取计时、harness墙钟及源码身份一并保存。

本轮只允许静态`node --check`，不以语法通过冒称页面、数值、图像或艺术关系已通过。
