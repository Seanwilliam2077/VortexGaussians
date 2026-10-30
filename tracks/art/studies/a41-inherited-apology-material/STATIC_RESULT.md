# A41 静态阻断：原桥接假设错误

2026-10-31。工程Agent art_a41_builder 核对后停止，未写四个实现文件，未运行浏览器、模拟或截图。root随后直接核对对应源码行，确认自己在BRIEF中的作用域假设有误。

demo/index.html的classic script在约282行进入严格模式IIFE，直到约4915行才闭合。sceneBurnState、researchScenePoints、srand、researchFrame等属于该IIFE的局部绑定，不是同源全局词法环境。外部classic script不能取得它们。

现有research.setScene在约3271行调用buildBurnState，约1080行重新建立全部材料数组。公开window.__demo没有恢复这些数组、burning前沿及emitCursor的入口。故本任务限定的“另加外部classic script而不改平台”方案不可行，不能满足原逐值继承合同。

没有采用重放、重新点火、重新栅格化、金色截图或只恢复燃料等替代。A41以static_bridge_scope_blocked结束，运行次数0、PNG0、模拟步0，没有材料可见性结论。此为实现资格的失败，不是对《道歉沿用》艺术价值的评分。

另一个实现合同必须明确如何把接口放在正确作用域以及如何保持旧作品来源；不得悄悄改A41条件再称原计划通过。用户允许的持续研究仍有效，是否值得准备这种普通接口另作决定。
