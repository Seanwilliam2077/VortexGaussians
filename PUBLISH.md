# 发布清单（GitHub Pages 上线前）

当前仓库为**私有**（论文双盲评审中）。公开发布步骤：

1. **Settings → General → Danger Zone → Change visibility → Public**（免费账号私有仓库开不了 Pages）。
2. **Settings → Pages → Deploy from a branch → `main` / `(root)`**，保存约 1 分钟后上线：
   `https://seanwilliam2077.github.io/VortexGaussians/`

## 发布前必改

- [ ] **匿名性**：作者栏当前为 Anonymous。等论文挂 arXiv 或录用后再公开，并替换 `index.html` 与 `README.md` 中 authors/affiliation 及 BibTeX。
- [ ] arXiv / Video 按钮当前为 disabled 占位；有链接后移除 `disabled` class 并填 href（`index.html` 与 README 徽章行同步）。
- [ ] 投稿版若重拍插图，同步 `static/images/`（源图在 `Research/paper/figures/`，压缩脚本见会话 scratchpad `build_site_assets.py` 思路：1200px JPEG q87）。
- [ ] `static/vortex_gaussians_paper.pdf` 与论文最新版同步（由 `Research/paper/build_docx.py` 生成）。

## 本地预览

```bash
python -m http.server 8000
# http://localhost:8000/         → 项目页
# http://localhost:8000/demo/    → 实时 demo
```
