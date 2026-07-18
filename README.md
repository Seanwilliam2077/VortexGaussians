# Vortex Gaussians — Project Page

Academic project page for **Vortex Gaussians: Real-Time Simulation-Driven Fire and Smoke as Native Gaussian-Splatting Content**, styled after the [FieryGS](https://pku-vcl-geometry.github.io/FieryGS/) / [Nerfies](https://nerfies.github.io/) project pages.

**完全静态、零构建、零外部依赖**——所有 CSS/JS 内联，图片本地，`git push` 后开 GitHub Pages 即可上线。

## 内容

```
index.html                      # 项目主页（自包含：内联 CSS/JS，含交互对比滑块）
demo/index.html                 # 实时 WebGL2 demo（单文件，页面上可内嵌启动，~83 KB）
static/vortex_gaussians_paper.pdf  # 论文 PDF
static/images/                  # 压缩后的论文插图（~650 KB 总计）
.nojekyll                       # 关闭 GitHub Pages 的 Jekyll 处理
```

页面章节（对照 FieryGS 结构）：标题/作者/链接按钮 → Teaser 三图 → Abstract → 管线与数字亮点 → **遮挡对比滑块**（FieryGS 同款交互）→ 两级涡解算 + 切片间耦合（含实测 0.21→0.39→0.61）→ 流驱协方差 → 定位对比表 → **点击即玩的内嵌实时 demo**（FieryGS 没有的差异化亮点）→ BibTeX → 页脚。

## 发布到 GitHub Pages（两步）

```bash
# 1) 在 GitHub 新建仓库（例如 VortexGaussians），然后：
cd VortexGaussians-page
git remote add origin https://github.com/<你的用户名>/VortexGaussians.git
git push -u origin main

# 2) 仓库 Settings → Pages → Source 选 "Deploy from a branch"，
#    Branch 选 main / (root)，保存。1 分钟后上线：
#    https://<你的用户名>.github.io/VortexGaussians/
```

## 发布前必改清单

- [ ] **匿名性**：论文在双盲评审期间，页面当前作者栏为 Anonymous。**接收/挂 arXiv 前不要填真名**；反之若已挂 arXiv，替换 `index.html` 中 authors/affil 两行及 BibTeX。
- [ ] `index.html` 中 `YOUR_GITHUB_USER` 占位符（Code 按钮链接）换成真实仓库地址。
- [ ] arXiv / Video 按钮目前是 disabled 占位，有链接后移除 `disabled` class 并填 href。
- [ ] Teaser 与结果图为当前 demo 实拍，投稿版若重拍图片记得同步 `static/images/`。
- [ ] BibTeX 在正式发表后更新为会议条目。

## 本地预览

```bash
python -m http.server 8000
# 打开 http://localhost:8000/
```
