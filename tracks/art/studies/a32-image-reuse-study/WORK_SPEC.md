# 《图用这一张》动作与材料规格

2026-10-31。依据 A32 BRIEF、A31 CREATOR_CHOICE 与 DECISION 制作。此文件描述实现的观看谱与接口，不预先判断艺术增量。制作仅新写本目录 `index.html`、`work.css`、`work.mjs`、本文件；旧作品与证据不改。

## 源与裁取

制作时使用 `view_image` 以原尺寸直接查看 A25 `inspection-01/04-request-returned.png`。其尺寸为 1360×1100。使用原 PNG 坐标 **x=47、y=296、width=944、height=471** 的黑色画布内区；排除原截图的标题、正文、请求卡、按钮和画布边框。初态窗口完整显示此区域，保留宁岚、叶青、沈舟三个旧名字与上方火形；不改变源像素。

SVG `viewBox="47 296 944 471"` 内仅引用这个原始 PNG。其父级 HTML 视窗向上收短，最终高度为源图 **214 像素**，即裁框下缘到原 PNG **y=510**。此线位于火形与旧姓名之间，三个旧名及下部反射全部退出配图。只移动下缘，不左右另裁，不重新生成任何位图。原 PNG 通过 `../a25-public-request/inspection-01/04-request-returned.png` 引用。

这是一张第 122 步的固定静帧。火形不变化；画面变化只来自视窗裁切、等比缩放、位移及新的 HTML 排字。最终火栏仍是同一 SVG/PNG 节点，位于纸面上部。署名不是源图名字的幸存像素；三名旧字都被裁去，宁岚与沈舟由新文字节点同字号、同色并署。

## 十四秒的一回观看

源图载入后停在 ready，等待 `#begin`；没有自动开始。elapsedMs 只记录实际运行中的呈示时间，暂停和结束不计时。

| 阶段 | 呈示时间 | 画面动作 |
| --- | --- | --- |
| source | 0–3000 ms | 完整源画布停留，三个旧名与火均可见。 |
| cropping | 3000–7000 ms | 下缘裁线从源高度 471 向 214 上行。前 880 ms 至 340；接着 2240 ms 至 222，较慢经过姓名行；最后 880 ms 至 214。各段平滑插值。 |
| placing | 7000–11000 ms | 同一窗口等比缩入竖幅纸的上部横栏。纸面于 7000–8200 ms 显现；正文与标题于 8200–10300 ms 排入；两署名于 9500–11000 ms 排入。 |
| posted | 11000–14000 ms | 完整告示停留；14000 ms 后停止 RAF，running=false，phase 仍是 posted。 |

纸上正文完整保留：“我们同意将小院的周六晚间开放给放映，并在闭场后共同收拾。”标题只使用现有事项“小院”“周六放映”，没有新增现实地址、日期、行动承诺或人物对白。

叶青的原话完整显示：“叶青：下次张贴时，请不要再列我的名字。正文由另两人保留。”它是纸面 article 的兄弟栏位，始终可读，不随裁取、排版、暂停或结束隐藏，不印进告示。桌面为纸外右栏；760 px 及以下变成告示上方独立栏位，允许滚动阅读，不承诺同屏容纳全部内容。作品说明在同一断点变单列。

`#pause` 暂停/继续只冻结或恢复当前 elapsedMs，不改变 phase。`#finish` 初态和进行中均可使用；它先结算最后一段真实运行时间，再令 ended=true、running=false、phase=ended，取消 RAF，当前图像与原话留在原处。结束不完成剩余步骤，也不模拟请求结果。正常到末尾仍可结束。无重播、跳段、advance、改内容投票或伪装过关方法。

隐藏页面时自动暂停；回到页面后需要按“继续”。改变视口只重新布置同一个呈示时刻。所有动画样式由同一时间变量写入，没有独立 CSS animation/transition 在暂停后继续。源静帧不启动模型、后台任务、计时轮询或持久存储。

## DOM 与只读接口

主要可见操作为 `#begin`、`#pause`、`#finish`。初态 begin 在图像载入前 disabled；pause 初态 disabled。开始后 begin hidden，pause 可用；正常 14000 ms 终点与 ended 后 pause disabled，结束后 finish disabled。`#colophon` 为可展开的来源和方法说明。

检查节点：`#stage`、`#notice`、`#paper-stock`、`#image-slot`、`#source-window`、`#source-art`、`#source-image`、`#crop-edge`、`#notice-print`、`#notice-body`、`#notice-signatures [data-signature]`、`#request`、`#request-text`、`#status`。`#stage[data-phase]` 同步当前 phase。

`window.__a32` 是不可重赋值、不可配置的冻结对象，仅公开 `snapshot()`；每次生成独立数据，没有暴露计时器或可写状态引用。读取不推进时间、不触发 render。它返回最近实际绘制/用户动作结算的时刻，运行时最多落后一个 RAF。

- `ready / phase / elapsedMs / durationMs / running / ended / lastAction / error`：实际状态。phase 只使用 ready/source/cropping/placing/posted/ended。源加载失败时 ready=false、error 给出原因、begin 不可用。
- `source`：相对路径、loaded、static=true、materialStep=122、PNG 尺寸、画布坐标、实际可见性与屏幕 rect。
- `clip`：原 PNG 坐标的 x/y/width/height/bottom、实际 crop progress、完整旧名在窗外的保守判断、裁线可见性。最后高度恰为 214 时才报告 allOldNamesOutside=true。
- `notice`：纸面可见性/opacity、原正文及可见性、placementProgress、窗口与图栏实际 rect 是否在 0.5 CSS px 内重合；每位署名的文本、可见性、实际 computed fontSize/color。
- `request`：完整文本、实际 CSS/祖先链可见性、通过 `notice.contains(request)` 求得的 insideNotice=false，另提供 fullyInViewport；可读可见性与是否正在屏幕内分开记录。

visible 表示元素尺寸非零且自身/祖先未通过 display、visibility、零 opacity 或 hidden 隐藏，并检查是否完全落在祖先的裁切范围之外；不把滚动出屏幕错误地记作删除原话。渐显中非零 opacity 如实记为可见，并同时提供纸面的 opacity。

## 实现与核验边界

原生 HTML、CSS、SVG 和无依赖脚本。`work.mjs` 使用无 import/export 的经典 defer script 引入，避免 file:// 模块跨源限制；因此可直接离线打开或从静态服务访问。字体均为系统字体回退，没有外部资源或安装步骤。

本实现者仅直接查看已有源图并进行静态检查；没有运行浏览器、页面截图、模拟、图像导出、外部检索或正式观众测试。静态核验的具体结果在交付时汇报。实际桌面顺序与窄屏初态/提前结束的唯一 UI 检查由 root 依 BRIEF 单独执行；不把静态核查视为连续观看效果或评分依据。
