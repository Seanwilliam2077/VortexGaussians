# A48 实施决定：原材料时钟，新普通格片呈现

2026-10-31，任何实现/装配/运行之前。Root全文读回BRIEF、AUTHOR_SPEC（含作者路径回应）、STATIC_FEASIBILITY，并独立读了原demo的点火、时钟、研究场景/reset/step/snapshot接口和A42装配先例。作者接受具体收窄。本决定允许下面的实现，待源码审计和封存后只执行预留的一次检查；不预认艺术资格或论文贡献。

## 明确采用的路径

采用作者新二维格片canvas作为作品的唯一画面，直接读取原demo的char材料值。原平台只提供材料状态与燃烧时钟；这不是原Gaussian渲染图、完整流体效果、真实纸燃烧或算法必要性验证。圆形命中格的失遮挡是事先编排，不是传播生成的新火形。原demo和A42等历史文件不改。闭包桥接由A42的一次纯插入装配模式建立，不能eval或复制一个伪燃烧器。

两片位置、旋转、线宽/线位、颜色、75×100局部格与4px格幅严格依AUTHOR_SPEC。F/B配对为同一(i,j)，顺序固定F的行优先7500点，再B的行优先7500点；id为F:i:j及B:i:j。源位置由画布(X,Y)映为[(X−360)/100,(360−Y)/100,z]，F z=0.5、B z=−0.5。元数据fuel=1、opacity=1、scale=0.02、color=[228/255,221/255,204/255]、areaWeight=0.0016，group为F/B。各向同性Gaussian只是源数据结构，画布不用其核。

新呈现可用两张300×400局部RGBA纸面缓存：底色或细线像素只被赋一次对应格的alpha，然后把B/F纸面依作者矩阵各drawImage一次到720×720不透明背景。细线中心34/162/234、宽2、v区间[20,380)，不得底色和线分别重复半透明叠加。8位canvas alpha量化属于普通栅格表示，原浮点char值完整保留；没有另加阈值、描边、阴影、修图或裁去越界结果。

## 唯一材料准备的完整参数约定

seed=20261031。完整参数定义为固定SHA原demo的RESEARCH_DEFAULTS，加以下全部覆盖；未列值逐键保留该固定源默认值，实际完整P必须进入记录：solver='vpm'，dimMode='layer'，layers=simLayers=1，ppl=1，paused=true，orbit=false，yaw=0，camElev=0，camDist=3.4，fov=0.85，sliceMode='world'；sceneOn=true、sceneMax=16000、sceneScale=1、sceneYaw=scenePitch=sceneLift=sceneOffX=sceneOffZ=0、sceneSH=0、box=false；spreadOn=true、spreadClockMode='elapsed'、spreadMeasureMode='legacy'、spreadParticlePolicy='block'、spreadBurnT=6、spreadRate=0、spreadFlameHeat=false、spreadSceneFeed=false、emitterOn=false、embers=false。原spreadR=0.11、spreadIgnR=0.14、frontier/sample/feed预算1400/160/48保持，不再优化。

只一次setScene、一次research.reset、一次__demo.ignite(-0.72,0.30,0.5,0.36)，随后一次research.step(360,1/60)。API step调用数1与积分步数360分别记录。原状、命中、准备后保存完整材料。实际命中集合应等于该球距离计算的F集合且非空；B及F未命中材料保持原五元组。实际char变化格须覆盖到u=0、完全落在W内；char依原值，不强制fuel/state/glow燃尽，不延长或补火。

## 动作与证据接口

普通页面自动完成唯一准备，加载遮盖在准备结束前保持。顺序为原状绘制/一次PNG导出/完整状态缓存，唯一点火和360步，准备后绘制/一次PNG导出/完整状态缓存，才显示作品与“恢复前片”。无隐藏advance/reset/ignite入口，无额外准备按钮。检查器与普通观看用同一路径。

唯一“恢复前片”按钮同步执行STATIC_FEASIBILITY规定的五数组原地对换、有序frontier原位置换、emitCursor原值保留和逐值/对象不变量审计；随后绘制并导出交换后唯一PNG。一次尝试即关闭按钮，失败不回滚或重试。历史全组计数留在发生地点，不随材料搬迁。没有第二次setScene/reset/ignite/step。完整世界hash可变，不以hash替代逐值检查。

作品页面只另设普通离开。异步PNG完成前后检查材料/物理状态一致；失败或离开使未完成任务终止，不重新启动。每阶段缓存原research.snapshot(detail=true)、完整源几何/元数据证据、frontier/cursor和所需独立物理证据。允许在最终文件中用明确共享引用避免重复保存完全相同几何，不能删掉逐点材料。只读接口window.__a48.inspect()返回脱离内部对象的记录；window.__a48.images()仅返回已经导出的三张PNG及身份/阶段，不生成新图。普通动作仅走按钮。

成本包含场景/源初始化、准备、各次绘图、PNG编码等待、交换与核对、记录读取和整体harness时间。源embed仍有只渲染的RAF，必须承认它存在；不发tick/reset消息，不宣称后台成本为零。离开取消宿主页任务、移除iframe、清理局部画布缓存，保留最终静态记录。context/browser/临时server最终全部关闭。不得启动常驻8137服务。

## 一次执行及角色

工程者可仅新增index.html、work.css、work.mjs、bridge.js、assemble.mjs、WORK_SPEC.md、.gitignore和inspect.mjs，后者按以上只读记录与一次真实按钮检查。可自行静态语法检查，不装配/打开页面/运行数值/生成图/提交。Root另请静态审阅者指出具体合同偏差，再全文核读，必要修正后封存源码。只能之后由root作一次装配与一次--execute。

单次整体检查≤120秒（含所有页面准备和导出），一个临时server/context，三张原720×720canvas PNG，总≤8MiB；无视频、截图替代、追加图、重跑、参数/几何搜索、外部资产/来源。源码与生成页身份在执行前后核对。超时或任何资格失败记录已发生动作与可得材料，关闭资源，不补跑。

取得实际三图后先交原A47作者作保留判断；作者保留才向原两位评分者同包咨询材料，是否允许完整论文由实际意见决定。没有新正式分数；A45双3/6、目标5/6和其他历史判断不改。工程成功与作者保留都不是接收证据。
