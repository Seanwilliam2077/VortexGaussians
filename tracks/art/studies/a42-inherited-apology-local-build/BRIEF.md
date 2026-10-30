# A42：在本地派生页面中显式放入继承接口

2026-10-31，准备前固定。A41的外部script方案因原平台IIFE私有作用域而静态失败，运行0；保留其[失败记录](../a41-inherited-apology-material/STATIC_RESULT.md)。本任务更换的是普通接口装配方法，不更改艺术判别或假装A41已通过。该工程开销只有在检验A40的实际材料问题时才有用途，不构成Art Papers或TOG贡献。

## 新装配合同

原demo/index.html保持逐字不动。输入固定314044字节、SHA256 e9d808c434bdd8ce91482f60502f03f5d08c56b71c082eb704c53275ff9f57d0。使用一个本目录assemble.mjs，验证输入hash以及唯一锚点“window.__demo = {”，把本目录bridge.js的明确源码插入该锚点之前，即原IIFE内部，产生本目录renderer.generated.html。这个派生页是一次性、透明的本地制作构建，不是原平台文件，也不是外部script能够访问私有变量。

生成文件只有原源码加一个标记包围的桥接块，不做其他替换，不eval、不改变iframe URL/嵌入语义。新index使用renderer.generated.html?embed=1&solver=vpm&orbit=0，以现有正常embed机制保持初始暂停。生成HTML约314KB，加入本目录.gitignore，不提交复制的整个平台；提交assemble、bridge和assembly.json（相对路径、输入/桥接/输出hash及字节数，不含私有绝对路径）使构建可复现。原平台与历史作品不变，生成文件已存在则拒绝覆盖。不得把其他脚本或未审过的字符串混入。

工程者先静态检查这种插入位置是否确在IIFE内部、初始化/嵌入顺序是否满足原平台语义，确认后才准备代码；若仍不可行直接停止。root读回代码、静态语法核对后，独占一次assemble，再一次材料检查。不在实现过程中偷偷生成、加载、模拟或截图。

## 保持的材料与成本合同

完整继承[A41 BRIEF](../a41-inherited-apology-material/BRIEF.md)的对象、字体/栅格/尺度/位置、两段原文、全部模拟参数、两次固定点火坐标、组名、逐值继承验证、按钮顺序和3+1.5+1.5秒预算；仅替换上面的装配方式及只读命名空间为__a42。原A41的“不复制整个平台”由本任务明确变更为本地生成一个不入Git的原源码派生页，不能追改A41。

严格继承的关键不变量：apology几何、id与完整材料逐值保留；新request完全未燃；release按作者编排移除；frame/time/RNG/particles/counters不变；只过滤移走点的frontier并保留其余顺序和emitCursor。不能重放、reset、重绘金色或仅恢复燃料。后续只在新行坐标点火，旧句仅受继续时钟及间接模型作用。2ignite/1reset/360steps/1handover，5PNG/8MiB，一次<=120秒，失败不重跑。

“可见继续变化”必须在旧句字面，而不是只在上方火团；不规定必须变暗或破损，亦不预支可读性。逐值继承/实际行为/旧句可读/旧句可见继续变化任一关键条件失败即收束当前提案；单有数值变化不足。静态工程阻断尚不等于已经观察到可见失败。不得以实现投入要求艺术保留或高分。

## 文件分工与输出接口

工程者只写本目录index.html、sample.mjs、bridge.js、assemble.mjs、WORK_SPEC.md、.gitignore，可引用A39 work.css。不得执行assemble或浏览器、改原demo或旧文件、检索/安装/commit。root写inspect.mjs并执行。若无需改变A41材料合同，不扩功能。

阶段固定ready→first-held(180)→handed(180)→later-held(270)→ended(360)，推进中running，错误error。按钮id=first/handover/later/finish，iframe id=source，canvas id=view。window.__a42只读ready/snapshot，顶层phase/frame/resetCalls/ignitionCalls/stepCalls/handoverCalls/hash/errors；material为research.snapshot({detail:true})完整结果，包含points/params/counters/particleStateHash，另列geometry、handover逐值验证和点火坐标/命中记录。每次绘制至多一步；隐藏/失焦停止，不能在背景偷跑。无隐藏推进或重置入口。

root检查前保存全部源码身份（含生成页与assembly.json）和固定五图序列，检查临时资源关闭、截图不推进、无外部请求/错误、所有计数及继承断言。模拟结果、图像与成本分开判定。此任务只给材料资格，尚未批准完整作品、论文或艺术评分；原两位评分者和旧分保留。
