# A41：继承道歉的单次材料资格

2026-10-31，执行前固定。承接[A40创作选择](../a40-material-handover-choice/CREATOR_CHOICE.md)。问题只有一个：受过接触的“我来迟了。”在换成新请求之后，只点燃新下行，旧句能否在仍可读时继续出现可辨变化？参数数值改变、文件身份保存、普通传递机制均不能替代可见材料判断。本页批准一份材料检查页及一次固定检查，不批准完整艺术作品、论文或评分。

## 对象、参数与编排

第一段两行是“我来迟了。”／“你先回去，不必等我。”，第二段两行是同一份“我来迟了。”／新造的“你再等一会，我就到了。”。全部原创虚构。下行更换是作者编排，不声称火删除旧请求。旧句不能重新栅格化、补点或以一张截图替换。新下行初始未燃；被移走的旧下行可以丢弃，不能声称整场完整物理状态移植。

继承A39的1200×600源画布、32px本地Microsoft YaHei字体、stride2/alpha>=128栅格、scale=q、opacity.94、color[.82,.78,.67]、fuel1、同相机/q/世界转换。每行anchorX=400，sourceY=276/324，其余栅格细节照A39。点id按group+采样位置稳定；第一句group=apology，前下行release，新下行request。apology几何只生成一次并原样复用。两组正文均在检查页实际可见，不以HTML代替材料字。

模拟与A39一致：seed20261031，dt1/60，elapsed时钟，legacy测度、block粒子策略，9层×160，graph1400/sample160/feed48，emitter关闭，spreadFlameHeat/sceneFeed开启，sceneMax16000，其余完整参数显式继承；无新时长/尺度/容量/燃烧速率搜索。两次固定点火radius.12：第一句source(480,276)，第二次只在新下行source(480,324)。新点火不得直接命中apology；若点位未命中或误中旧句，记录失败，不移动点位重试。图传播和火焰热对旧句的间接影响属于实际模型。

检查页是材料仪器，不能称完整观看体验。只有固定动作按钮：first推进180步；handover在frame180替换下行且零步；later点燃新下行并推进90步；finish继续90步且不再点火。每次绘制至多一步，失焦/隐藏不额外推进；若因此未完成则记录失败。计1reset、2ignite、360steps、一次handover。初态、首段3秒、刚换行仍3秒、后段4.5秒、终态6秒，各保存一图。不可变为六秒后再找结局。

## 局部普通桥接

root只读发现research.setScene会新建燃烧数组，现有公开接口没有继承状态入口。允许在本目录新增一个普通classic-script桥接文件，在本次iframe载入后显式注入，借同源页面既有全局词法环境访问内部数组；不eval、不修改demo/index.html、不复制整个平台、不改旧作品。该方法是局部制作工具，不是算法贡献或通用物理检查点。

桥接只允许一次固定组更换：先校验id、完整apology几何/原始燃料元数据未变、同一seed/frame和legacy配置，保存旧句h/fuel/glow/char_/state与前沿id次序；调用已有setScene为“旧句+新request”建几何，原样恢复旧句数组和仍保留的burning前沿次序及emitCursor。新request保持未燃。保留已有粒子、时间、随机数和累计计数；legacy areaFeedCredit应为0。不得偷偷reset、step、ignite、重播或估算颜色。移除旧下行及其frontier明确记录。

必须记录并断言：前后每个apology点完整元数据与材料值逐值相等、点数/位置/尺度未改、particleStateHash/时间/frame/随机数/计数未改；新增request全state0、heat/char/glow0/fuel1；只移除了release并新增request。后续变化另测，不能以handover的状态保持推出后续可见变化。任何断言失败立即停止。

## 实现和检查预算

实现者只写本目录 index.html、sample.mjs、bridge.js、WORK_SPEC.md，可引用A39的work.css但无需复制。暴露window.__a41只读ready/snapshot，包含phase、frame、resetCalls、ignitionCalls、stepCalls、handoverCalls、完整点分组、原材料/粒子hash、counters、geometry、handover逐值核对与错误；不提供隐藏推进入口。按钮id固定为first、handover、later、finish；源iframe id=source，显示canvas id=view。root独占inspect.mjs和一次执行，先读回实现与桥接后才运行。

单次新inspection-01目录，不覆盖或重跑，<=120秒、<=5PNG/8MiB；正常UI点击固定四按钮，不直接注入模拟状态。截图前后状态须完全保持，无额外模拟；记录源码SHA256、完整阶段状态与成本、所有错误/外部请求，关闭context/browser/临时server。可以做必要静态语法核对，无额外数值尝试或隐藏预运行。

材料动作通过与艺术保留分开。桥接正确不代表资格通过；root和作者直接比较实际03/04/05旧句字面，同时查看新旧内容关系。若只有稳定金色或数值变化、旧句不再可读、无继承、直接误点旧句或工程失败，保存并收束当前提案，不补参数/时长/路线。只有实际材料条件支持，才另决定完整作品；本次不索正式分。旧A39两个3/6、所有历史文件与TOG/main保持。
