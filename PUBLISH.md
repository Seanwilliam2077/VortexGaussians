# 发布状态与清单（GitHub Pages）

仓库已**公开**，Pages 从 `main` / `(root)` 部署：
`https://seanwilliam2077.github.io/VortexGaussians/`

## 已完成

- [x] 仓库转 public（免费账号私有仓库开不了 Pages）。
- [x] Settings → Pages → Deploy from a branch → `main` / `(root)`。
- [x] `static/vortex_gaussians_paper.pdf` 与论文同步。**注意生成方式**：站点版由
      `Research/paper/web.tex` 编译（= `main.tex` 去掉 `review` 选项），所以没有评审行号；
      投稿版仍是 `Research/paper/main.pdf`（`acmtog,review,anonymous`，18 页）。
      论文一改就要重跑：`cd Research/paper && pdflatex web.tex`（跑两遍）再拷过来。
- [x] `static/images/` 与 `Research/paper/figures/` 同步（1600px 宽、JPEG q87；
      重建脚本见下）。README 头图 `teaser.jpg` 由三张 teaser 面板重新拼接。
- [x] Video 按钮已接上 `static/video/vortex_gaussians_supplemental.mp4`（95 s，1080p 源）。

## 仍待办（需要作者本人决定）

- [ ] **去匿名**。页面与论文目前都是占位的 Anonymous，公开后同样显示占位。要填真实信息需改四处：
      `index.html` 的 `<p class="authors">` / `<p class="affil">` / 底部 BibTeX 的 `author =`，
      以及 `README.md` 的作者行与 BibTeX。论文侧则是 `main.tex`/`web.tex` 去掉 `anonymous`
      并补 `\author{}` 块。**双盲评审期间是否去匿名由投稿政策决定**。
- [ ] **arXiv 按钮**仍是 `class="btn disabled" href="#"` 占位；有链接后去掉 `disabled` 并填 href
      （`index.html` 与 README 徽章行同步改）。

## 资产同步脚本

图片刷新（把 `paper/figures/` 的当前版本压成站点版）：

```python
# 在 Research/ 下运行
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
for p in "" "demo/" "static/vortex_gaussians_paper.pdf"; do
  curl -s -o /dev/null -w "$p %{http_code}\n" "https://seanwilliam2077.github.io/VortexGaussians/$p"
done
```

Pages 从 Linux 提供服务，**文件名大小写敏感**；本地 Windows 不区分大小写，所以
新增资产后一定要跑上面的自检，别只在本地点一遍。
