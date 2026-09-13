# 删除第四问重复剖面图

用户明确同意删除原图10，理由为其信息已由结果表和时空对照图覆盖。修改仅涉及 `paper/guosai2026/sections/06_q4.tex` 的原剖面图块和前导图引用；题定表、模型数值、三张示意图及四张用户原图均保留。

原 `fig_q4profiles` 标签及正文引用已移除，`fig_q4_control` 自动从图11改为图10，位于第24页。图片文件 `q4_C_profiles.pdf/.png` 保留为历史来源，不再由正文引用。变更前章节备份位于 `ARCHIVE_all/paper_before_remove_q4_profile_20260913/06_q4.tex`。

基于当前工作区最新精简正文，使用 XeLaTeX/latexmk 编译阅读版31页、完整版113页。两版共有31页文本一致，10个图号全部解析，无未定义引用、重复标签或 Overfull/Underfull；删除后第23、24页已渲染检查，结果说明和对照图衔接正常。机器检查见 `REMOVE_Q4_PROFILE_CHECK_20260913.json`。

正式入口为 `paper/guosai2026/reading.pdf`、`main.pdf`；`review/` 中旧审阅快照不覆盖。用户授权本次删除，不代记全文终审。
