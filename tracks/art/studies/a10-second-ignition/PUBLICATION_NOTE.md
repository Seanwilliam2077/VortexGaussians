# 发布时追加核对

root在制作文件停止编辑后读取原解码stderr，发现17条null输出muxer的DTS非单调诊断（2,067字节）；原命令确实退出0，但“全解码通过”不能被读成日志无诊断。原命令、结果、日志和制作文稿保持原样。

首次追加ffprobe的JSON输出在解析时失败（line1201/column10），[原输出](run-01/frame-timing.stdout.json)保留；root初写本说明时先写入了尚未完成核对的299帧结论，尚未封包或发布即发现并更正，不能算第一次核验成功。随后一次flat格式读取现有影片的299个视频帧记录，presentation timestamps严格递增（0至83.426秒）。见[追加收据](run-01/decode-diagnostic-addendum.json)及[flat输出](run-01/frame-timing-flat.stdout.log)。没有重录、重编码或新模拟，也不以此确定任何播放器中的观看体验。实际九帧中的20.02秒偏移继续保留。

root另目视10秒、30秒、再次点火后及31秒末帧；与制作／反思Agent一致，晚态仍以醒目火焰为中心，二次点火未增加点的区别主要由状态文字说明。此材料排练不被包装成新艺术贡献。
