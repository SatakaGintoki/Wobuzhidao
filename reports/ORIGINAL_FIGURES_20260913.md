# 恢复用户原图

版本 `paper-spacetime-original-v1`。用户反馈重绘版不如其提供的原图清晰、美观。结合此前“那就放进正文”的采用指令，本次使用用户四张原始 PNG 替换重绘 PDF，保留原布局、字体、配色、文字和原始像素。重绘版 `paper-spacetime-v1` 记为 `REVISION_REQUESTED`，不再由正文引用。

## 来源与位置

来源目录为 `C:/Users/chens/Desktop/组员的论文修改/图片/`；原图无缩放、裁剪或重新编码，直接复制到根目录和论文内的 `figures/`。

| 用户原文件 | 正文图片 | 原始尺寸 | 图号/页码 |
| --- | --- | --- | --- |
| 微信图片_20260913121806_72_219.png | q1_spacetime_original.png | 4789×1728 | 图4/第10页 |
| 微信图片_20260913121806_73_219.png | q2_spacetime_original.png | 4789×1728 | 图5/第13页 |
| 微信图片_20260913121806_74_219.png | q3_spacetime_original.png | 2752×1920 | 图7/第16页 |
| 微信图片_20260913145849_626_161.png | q4_spacetime_comparison_original.png | 4800×1984 | 图11/第24页 |

原图与数据的核对证据沿用 `EXTERNAL_FIGURE_AUDIT_20260913.md`，不声称掌握组员原绘图代码。三张技术示意图与其他结果图保持。第四问移除重绘版额外的(c)面板引用，正文和图注保留同附录4物性、左右时间轴不同、计算含水率与实测半径的区别以及严格报告时刻说明。

## 检查与交付

- 复制文件 SHA256 与用户原文件一致。
- 使用 pypdf 提取最终阅读版 PDF 中的图片，逐一转换为 RGB 后比较像素 SHA256，四图尺寸和全部像素均与原 PNG 一致，证明 PDF 嵌入未降低分辨率。
- 四个正文页面已渲染检查，无裁切或重叠；11个图号及引用检查通过。两版正文文本一致，编译无 Overfull/Underfull 或未定义引用。
- 正式阅读版为32页、完整版为114页。编译使用当前工作区已压缩的最新正文，本次没有恢复旧章节或将页数变化全部归因于换图。
- 替换前章节和 PDF 位于 `ARCHIVE_all/paper_before_original_figures_20260913/`；检查文件为 `ORIGINAL_FIGURES_PAPER_CHECK_20260913.json`，渲染页位于 `_tmp/original_figures/paper/`。

正式入口仍为 `paper/guosai2026/reading.pdf` 与 `main.pdf`。本次只修正图形采用与对应图注，不改变模型、结果表或数值。用户对修正后整体观感的终审未代记。
