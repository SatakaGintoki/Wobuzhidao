# 论文字体命令泄漏与乱码修复

日期：2026-09-13。范围：正式目录 `paper/guosai2026/` 的编译设置和两版 PDF；未修改模型、结果数值、正文段落或图片。

## 原因

修复前 `main.log` 首行记录 15:29 使用 pdfTeX / pdflatex。导言区第8至10行的 `IfFontExistsTF`、`setCJKmainfont`、`setmainfont` 等命令在该引擎下未定义；日志同时报告 CTeX Fandol 字体集不可用和缺少 `begin{document}`。错误后仍继续排版，导致第一页实际出现 `SimSun[AutoFakeBold]SimSun[AutoFakeBold]SimHei Times New RomanTimes New Roman ConsolasConsolas`。修复前已从 PDF 第一页提取到该字符串。

## 修复

- `main.tex`、`reading.tex` 首行明确声明 XeLaTeX。
- `preamble.tex` 在载入文档类前使用 `iftex` 的 `RequireXeTeX`，错误引擎直接停止。
- 项目 `.vscode/settings.json` 将 LaTeX Workshop 默认流程设为 `latexmk (XeLaTeX)`，启用遇错停止；不修改用户全局编辑器配置。
- 论文 README 补充正确编译方式。沿用原有 `latexmkrc`，由 latexmk 重复编译至交叉引用稳定。
- 重新生成正式 `main.pdf` 与 `reading.pdf`，完成引用收敛。

## 核验

完整版117页，阅读版35页。两版日志均确认使用 XeTeX；未发现未定义命令、缺字、未定义引用、未定义引文或 Overfull 溢出。全文提取未见 Unicode 替换字符，正文及数学附录未见字体配置名称、`AutoFakeBold`、`&#x20;`、`??` 或 `[?]`。

完整117页已渲染成接触表检查；另放大检查首页、图示与公式页及附录页面。未见本次字体命令泄漏及乱码问题。完整版前35页与阅读版逐页像素比较一致。

在独立临时输出目录故意运行 pdfLaTeX，返回码为1，明确提示 XeTeX 必需，没有生成 PDF，确认保护生效且没有覆盖正式文件。

机器核验、提取文字与渲染图片位于 `_tmp/font_compile_fix/`，结果为 `verification.json`。此检查针对编译与显示，不代替论文内容的人工终审。

- main.pdf SHA256：`82a9631e0a0ec0cbef3fe902883b15a0df5146fb8038eb5c308a843dcc4fca63`
- reading.pdf SHA256：`01a19b9188a16ea9aa5ecbcb22b83661328e38fe86b60b63b1934dab760eef51`
