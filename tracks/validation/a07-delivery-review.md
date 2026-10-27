# A07 delivery review

27 October 2026. Independent root review of the existing [A07 film](../art/studies/a07-return-and-record/run-01/study.mp4); no new browser, simulation or encode.

The original edit run remains `failed`: encoding returned zero, but parsing the saved ffprobe JSON failed because its final outer closing brace is absent. The later flat-format metadata read and frame extraction are recorded separately in [inspection.json](../art/studies/a07-return-and-record/run-01/inspection.json). This does not relabel the original run.

Root independently matched all ten original source/tool/plan hashes against `sourceBefore`, `sourceAfter` and disk. The delivered MP4 SHA256 is `dd218e6b994b94126f348be74a2f3564ae562ebf0f2980deb0037cb66f4541db`. Four decoded frames at 1, 15, 17.5 and 22 seconds were visually inspected: the title and disclosure are readable; the final scene and the prior-operation receipt are both visible; receipt values10.00s/3,320/1,400 are not cropped. The material remains soft, with a local dark change partly occluded by flame. This is a presentation review, not evidence of human artistic response.

A complete read-only decode then used the installed FFmpeg7.1.1, mapping video stream0 to the null output. Command arguments from the repository root:

```text
ffmpeg.exe -hide_banner -v error -nostdin -i tracks/art/studies/a07-return-and-record/run-01/study.mp4 -map 0:v:0 -f null - -progress pipe:1
```

The command returned0 with no decoder error text. Final progress reported623 frames, `out_time=00:00:24.920000`, `dup_frames=0`, `drop_frames=0`, and `progress=end`. This verifies that the complete existing video decodes; it is not a benchmark or a second encode. No layout repair was required.
