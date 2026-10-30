# A45《空心》制作规格

2026-10-31，唯一检查前的实现说明。依 [BRIEF](BRIEF.md)、[AUTHOR_SPEC](AUTHOR_SPEC.md) 及 [A44 创作选择](../a44-form-selection/CREATOR_CHOICE.md) 固定实现。此页不宣称构图已经成立，也没有以工程完成替代作者选择。制作工程者仅写本目录四个实现文件，未运行页面、求解、截图或录制；实际结果由 root 独占的一次检查另记。

## 原图像与唯一源准备

原 `demo/index.html` 与历史作品不改。iframe 以 `../../../../demo/index.html?embed=1&solver=vpm&orbit=0` 正常载入；原 embed 分支置暂停，原 loop 只重新安排自身回调而不求解或绘制。A45 不发送 tick/reset 消息，不用派生平台、桥接、eval、PLY 或文字场景。

准备使用公开 `__demo.forceSize`、`research.reset`、`research.step`、`__demo.render` 和 `gl.finish`。参数覆盖逐项取自 A20 `room.mjs` 的 startFire：solver=vpm、dimMode=layer、layers=simLayers=9、ppl=160、paused=true、orbit=false、yaw=0、sliceMode=world、emitterOn=true；spreadOn/spreadFlameHeat/spreadSceneFeed/sceneOn/box 均 false；camDist=4.4、camElev=.12、mode=fire、exposure=1、bloom=.65。其余参数由原 research.reset 的 RESEARCH_DEFAULTS 提供，实际完整 params 进入 sourceInitial/sourceParams/sourceAfterPreparation。没有手改私有状态、setScene 或点火。

seed=20261030、dt=1/30。正常 iframe load 后仅准备一次、reset 一次、step150 次，每次 step(1,dt)。F1 是第一步之后的图，F150 为五模拟秒末态，不缓存 F0。每步立即 render/gl.finish，然后在同一调用栈同步 drawImage 到唯一640×480的2D暂存 canvas；这样取像在 WebGL 后缓冲可能被浏览器清除之前完成。随后 createImageBitmap(暂存)，等待完成才进入下一步，每步另以 setTimeout(0) 让出事件循环。整个过程中不保留第二套帧集或磁盘源资产；不改变重力或再次运行四份火。

150个640×480 RGBA源帧的名义负载为184320000字节。唯一暂存另计1228800，持久帧缓存合计185548800，低于192MiB（201326592）。源 canvas 名义1228800、作品 canvas2073600及最大单次临时像素读取2073600另列。此账不是进程、显存、ImageBitmap实现或编码器的实测峰值；PNG/WebM和编码暂存也不能称为免费。

准备记录逐步物理 hash/particleStateHash、粒子数、step/render/同步拷贝/bitmap/让出时间以及完整初末物理快照、完整参数和准备墙钟。ready Promise 只在150帧全部完成后兑现。准备错误立即停止，保留已经发生的调用和错误，关闭缓存，不重做。root 的整体≤150秒预算包括这段准备，不借预运行藏掉成本。

## 原生构图

作品 canvas 固定720×720、纯黑背景；CSS只能整体等比缩小。底边完整640×480源图以1.125倍画为720×540，左上角(0,180)，裁切路径依次为(0,720)、(720,720)、(480,480)、(240,480)。各区用 save/translate/rotate/clip/drawImage/restore 同时旋转图和裁切，绕(360,360)顺时针转0°、90°、180°、270°，绘制顺序为下、左、上、右，符合作者表中的四个梯形。

最后覆盖中央(240,240,240,240)的纯黑不透明矩形。每次正常合成读取该区域全部57600像素，逐个验证RGBA=(0,0,0,255)，记录次数、总检查像素、异常数与时间。旋转裁切没有透视挤压、接缝线、滤镜、锐化、补火、纸色或暖光覆盖；浏览器默认平滑保留。它是同源画面的编排，不是四个向心物理火场。

画布内没有文字、计时器、阶段标签、箭头、音频或记录界面。标题、普通播放/暂停/离开及简短来源说明位于画布之外；记录内容只在只读接口和后续检查包中。

## 唯一正常呈示

ready 后正常点击 `#play` 开始一次呈示。首次正常合成 t=0 取F1。活动时间为 monotonic performance.now 减去播放起点及主动暂停墙钟，不能按完成了多少次RAF推进时钟。t<10 的未锁区取 `min(150,1+floor(15t))`，对应 Fn 的左闭右开区间 `[(n−1)/15,n/15)`；没有插值、倒放、补帧或循环。

冻结先于该时刻合成执行：上在4秒锁F60，右在6秒锁F90，下在8秒锁F120，左在10秒锁F150；10到22秒保持此终幅。每次回调均按当时实际活动时间取图，即使迟到也不回画理想端点。首次达到或超过22秒的正常回调仍合成并记录终幅，随后停止；实际迟到和停止开销明确记录，不增加有意延长。每次合成都记录活动时间、墙钟、RAF时间、四区源索引、与上次间隔、绘制耗时及中心检查。回调日志只证明调用过合成，不证明显示器扫描或人眼逐帧观看。

各区源索引若跨过一个以上帧，missedIntervals 列出未被该区正常合成选用的索引范围及理想区间、前后实际时间。冻结首次被合成时记录实际时刻、迟到、上一次显示的索引及预定停格帧此前是否真的合成过，不能用帧已在缓存证明它曾被观看。四区停格始终按固定帧取值，不因漏显换成别的好看帧。

`#pause` 是普通主动暂停：停止RAF、记墙钟，正常播放按钮变为继续；同一次原生录制可暂停/恢复，源求解不再发生。恢复仅从缓存继续。隐藏、失焦不会冒充主动暂停来冻结艺术时钟：活动准备/呈示/暂停阶段发生这些事件会终止这次活动并记缺口，不自动追赶或重启。ready等待本身不是活动呈示。`#leave` 随时结束，普通终态仍保留画布末幅，主动离开才隐藏画布。页面不提供重播或重置。此次正常检查不为了覆盖分支再暂停、离开或第二次播放，未实测分支须如实另列。

## 六图与一次可选原生录像

目标画布抓帧为2/4/6/8/10/22秒。首次正常合成达到或越过目标时，立即调用原 canvas.toBlob；它保存当时真实画布，不等待后续再重画理想目标。记录目标时刻、实际合成时间、实际捕获墙钟、迟到、四源索引、合成序号、原生720×720尺寸、PNG字节与SHA256、全幅RGBA像素FNV1a32及编码完成时间。actualSeconds 是当次真实回调开始选图的时间；drawCompletedSeconds 另记绘制返回时间，captureInvokedSeconds/captureLateBySeconds 另记抓图调用位置与迟到，不把任一字段冒充显示器准确扫描或人的观看时刻。

一次回调跨过多个未取目标时，只保存最新目标对应的这一张正常画布，较早目标标为missing。不复制多份同一证据、不补拍、不截取浏览器页面、不裁图或挑选。PNG累计≤8MiB，超限/编码失败保留failed字段，不缩图或另取画面。10秒和22秒记录各自实际图像像素hash并比较；相同只支持两次取图相同，不能单独证明十二秒连续观看。

普通播放开始时只尝试一次 `MediaRecorder`，唯一请求格式为 `video/webm;codecs=vp9`。支持检测false则记录unsupported；否则仅 canvas.captureStream(30) 的视频轨、无音频，固定请求2000000 bits/s，start(1000)分块。每次正常RAF在末12秒仍绘同一终幅，让这一静置也进入同一段录像的时间轨，而不是另做十秒文件。录制记录start/stop/pause/resume/data/error事件实际墙钟、chunk时间与大小、轨道设置和终止状态。上限16MiB；超限或编码失败停止媒体轨并保留错误，不换codec、编码器、重新播放或替代文件。媒体失败独立于正常画布呈示，不要求重跑作品。

到呈示结束时先进入 `phase=finalizing`，立即请求录制stop并关闭stream，等待尚未完成的PNG、原生onstop和recordedBlob；随后生成已有blob的SHA256/base64。停止事件最多等待6秒，元数据最多3秒，超时仅记录缺口。没有在这些等待中继续呈示或计算源。对产生的WebM用一个不播放的临时video读取元数据/尝试首帧decode，记录实际尺寸、可得duration和其非有限/不可得状态、可得quality字段；不调用play，也不把这个探针当连续观看。URL及时撤销。编码完成、首帧可解码、实际连续观看分别陈述；本代码从不声称后者。

## 接口、完成与资源关闭

`window.__a45` 冻结且只有 `ready` Promise、`snapshot()`、`artifacts()`。没有advance、seek、restart、reset或专用检查按钮。读取接口不绘制、不编码、不访问新媒体、不推进物理、不启动录制，不读动态墙钟。所有墙钟仅由实际动作记入状态。

snapshot 完整保留 phase、准备/reset/step/ignite/render/bitmap/play/pause/leave/合成/抓帧调用数、seed/dt、requestedParams与实际sourceParams、sourceInitial、sourceAfterPreparation、sourceAfterPresentation，以及 material（源仍在时现场只读快照，关闭后是已保存终态）。呈示结束读取原物理末态，与准备后完整原快照逐值核对 sourceUnchangedDuringPresentation，含原hash/particleStateHash、随机计数、参数、粒子/累计计数等；然后才移除源iframe并释放引用。

此外保留 preparation成本、memory名义账、playback时间/暂停/停止原因、displayLog、missedIntervals、freezes、captures、center、terminalPixels、recording（含独立错误）、总成本、cleanup、events、errors。PNG与视频的base64不重复放在snapshot。

artifacts() 返回：

```text
{
  artifactsReady,
  images: [{ file, targetSeconds, actualSeconds, lateBySeconds, sourceFrames,
    compositeSequence, capturedWallMs, captureInvokedSeconds, captureLateBySeconds,
    drawCompletedSeconds, width, height, bytes, sha256, pixelHash,
    mime: "image/png", dataURL }],
  video: { file, mime, bytes, sha256, base64, metadata,
    requestedWidth, requestedHeight, startedWallMs, stoppedWallMs,
    recordWallMs, pausedWallMs, terminalContentSeconds } | null,
  captureRecords,
  recordingStatus
}
```

这里只返回已经产生的压缩PNG及可选WebM，不临时补出缺图。图按目标时间排序。normal-presentation.webm 的 metadata 可说明尺寸/时长是否实得；requestedWidth/Height只是请求尺寸，不替代解码结果。

正常22秒停止后，清除自有RAF，关闭所有ImageBitmap和单份暂存，停媒体轨、移除源iframe（同时终止其空闲embed回调），保留作品canvas末幅和记录。异步仍在创建的bitmap完成后立即close，不进入帧集。PNG/媒体完成或独立失败、资源关闭状态记完，才置 `artifactsReady=true`、`phase=ended`。提前离开或致命中断则最终为left/error，保留已得材料；普通媒体失败可在ended中记录failed/unsupported。cleanup报告逐个创建/关闭数、in-flight、live count、stream/recorder/源释放情况，不能拿调用close代替已核验状态。

## 唯一检查与尚未判断的部分

root 在完整读回与静态语法核对之后，独占一次≤150秒检查：一个临时本机server、一个browser context，load→await ready→正常点击play→等待ended及artifactsReady→只读导出→关闭。保存源码前后hash、所有错误/外部请求、完整状态与实际媒体成本，禁止网络外取。任何失败保留阶段和缺口，不同名覆盖或走第二条路径。

静态实现不证明四边火形足够、中央被勾出、逐边停格被感到、末幅值得停留；也没有连续观看证据。普通万花筒/屏保解释仍保留。源求解、构图、日志与录制成本各自陈述；实际原图和运行记录先交原创作者决定是否保留，再按root合同交原评分者，不因实现投入预支艺术分数。
