# 发布状态与清单（GitHub Pages）

仓库已**公开**，Pages 从 `main` / `(root)` 部署：
`https://seanwilliam2077.github.io/VortexGaussians/`

## 已完成

- [x] 仓库转 public（免费账号私有仓库开不了 Pages）。
- [x] Settings → Pages → Deploy from a branch → `main` / `(root)`。
- [x] `static/vortex_gaussians_paper.pdf` 与论文同步。**注意生成方式**：站点版由
      论文源树里的网页版 `.tex` 编译（去掉评审行号选项）。论文一改就要重跑
      `pdflatex`（跑两遍）再把 PDF 拷进 `static/`。论文源不在本仓库。
- [x] `static/images/` 与 论文图目录 同步（1600px 宽、JPEG q87；
      重建脚本见下）。README 头图 `teaser.jpg` 由三张 teaser 面板重新拼接。
- [x] Video 按钮已接上 `static/video/vortex_gaussians_supplemental.mp4`（95 s，1080p 源）。

## 仍待办（需要作者本人决定）

- [x] **去匿名（站点侧已完成）**。`index.html` 的作者/单位/BibTeX 与 `README.md` 的作者行与
      BibTeX 均已填 Zijun Xiao / Georgia Institute of Technology / zxiao316@gatech.edu，
      引用键统一为 `xiao2026vortexgaussians`。
- [x] **去匿名（论文侧已完成）**。站点 PDF 已重编：`static/vortex_gaussians_paper.pdf`
      31 页，首页署名 `ZIJUN XIAO, Georgia Institute of Technology, USA`，
      无评审行号、无未解引用、`Anonymous` 零残留。
- [ ] **arXiv 按钮**仍是 `class="btn disabled" href="#"` 占位；有链接后去掉 `disabled` 并填 href
      （`index.html` 与 README 徽章行同步改）。

## 资产同步脚本

图片刷新（把 `paper/figures/` 的当前版本压成站点版）：

```python
# 在论文源树的上级目录运行
import os
from PIL import Image
SITE, FIG, MAXW, Q = 'VortexGaussians-page/static/images', 'paper/figures', 1600, 87
for n in os.listdir(SITE):
    base = os.path.splitext(n)[0]
    if base == 'teaser':          # 头图是三联拼接，单独重建
        continue
    src = next((os.path.join(FIG, base + e) for e in ('.jpg', '.png')
                if os.path.exists(os.path.join(FIG, base + e))), None)
    if not src:
        continue
    im = Image.open(src).convert('RGB')
    if im.width > MAXW:
        im = im.resize((MAXW, round(im.height * MAXW / im.width)), Image.LANCZOS)
    im.save(os.path.join(SITE, n), quality=Q, optimize=True)
```

## 本地预览

```bash
cd VortexGaussians-page && python -m http.server 8137
# http://localhost:8137/         → 项目页
# http://localhost:8137/demo/    → 实时 demo
```

## 上线后自检

```bash
for p in "" "demo/" "compare.html" "study/" \n         "static/vortex_gaussians_paper.pdf" \n         "static/video/vortex_gaussians_farmland_ov.mp4" \n         "static/images/farmland_ov_poster.jpg"; do
  curl -s -o /dev/null -w "$p %{http_code}\n" "https://seanwilliam2077.github.io/VortexGaussians/$p"
done
```

Pages 从 Linux 提供服务，**文件名大小写敏感**；本地 Windows 不区分大小写，所以
新增资产后一定要跑上面的自检，别只在本地点一遍。
