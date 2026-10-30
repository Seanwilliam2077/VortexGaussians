# A50实际来源访问账

2026-10-31。这里只记录实际调用，不将失败路径或目录当正文阅读。无下载、作品运行、截图或新媒体。

Root一次检索含两query：

1. `site.s2026.siggraph.org art papers evaluation criteria contribution`
2. `site.artpapers.siggraph.org 2025 PDF artist paper`

随后一次open https://s2026.siggraph.org/program/art-papers/ ，得到371行HTML正文，直接读取类别及评审标准。无新作品全文。

独立非评分读者一次检索含两query：

1. `SIGGRAPH "Art Papers" memory material PDF author`，域名过滤siggraph.org、direct.mit.edu、dl.acm.org。
2. `"SIGGRAPH" "Art Paper" "pdf" computational art memory`，无域名过滤。

其三次open依次为：

1. https://history.siggraph.org/wp-content/uploads/2023/02/SIGGRAPH-2015-Leonardo.pdf 。返回解析元数据34页/1374行，实际可见L0—L456，封面、出版信息、目录和引言；目录支持Temkin论文身份及起页375，未读正文。
2. 同一PDF首次引用、lineno450，返回`(400) Timeout fetching`，没有新增正文。
3. https://history.siggraph.org/wp-content/uploads/2007/01/SIGGRAPH2007_Art_Gallery_Catalog.pdf.pdf ，返回`(400) Content length is too large: 14419936`，没有可读正文。

读者没有click/find/截图/下载，未重开已闭合题名。选0篇。Root仅核读该账，未为获取目标正文再打开上述PDF。A50实际完成的是标准和尺度解释；完整已发表作品论文阅读仍缺。
