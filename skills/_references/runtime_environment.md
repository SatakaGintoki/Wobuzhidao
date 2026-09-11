# 实际运行环境与路径

在需要代码、绘图、编译或验收时读取。已有有效环境记录直接复用；纯讨论和建议题不为通过环境清单安装计算/排版工具。

## 解释器和命令

- 先使用项目已选择的解释器、虚拟环境或宿主提供的运行时。缺包时检查另一个已知可用解释器，不递归扫描整台机器，也不直接全局安装一套依赖。
- Windows PowerShell 用 `Get-Command python,python3,py -ErrorAction SilentlyContinue` 定位候选；必要时 `py -0p` 查已注册 Python。验证实际路径后使用 `& $pythonExe ...`，其中 `$pythonExe` 为已发现的路径。Bash 用 `command -v python3` / `command -v python`，随后 `"$python_bin" ...`。不要将 Bash 的 heredoc、`command -v`、`&&` 示例直接交给不支持它们的 PowerShell。
- `python -m pip` 必须由选定解释器执行，不能用可能指向其他环境的裸 pip。只在用户已有安装授权或明确批准具体缺失项后安装；保留已批准范围，不自动切换包管理器批量安装全部可选工具。
- 将 Python 绝对路径、版本、所需包版本和外部命令路径记入 `plan.md` 的环境小节或已有运行报告，并由 STATE 索引。不为同一环境反复新建报告。

## 分阶段检查

可使用 [只读环境检查脚本](../doctor/scripts/check_environment.py)。用选定 Python 执行，`--phase modeling` 对数值/绘图常用包检查；按本题额外传 `--require-package openpyxl` 等。`--phase writing --engine latex` 或 `--phase verification --engine typst` 只检查对应阶段所需工具。`--tool 名称=绝对路径` 可登记不在 PATH 中的已知工具。

脚本的包导入结果与命令路径是环境证据，不是编译/渲染通过证明。建模阶段不要求先装论文编译器；最终验收需要选定编译器和可用的 PDF 栅格化工具（或已经实际验证的等价能力），缺失时记相应项未执行，不能声明提交就绪。

## 首次排版

- 模板复制到赛题工作区后，核对字体、宏包及实际编译目录。只调整工作区副本，保留捆绑模板来源。
- `fontset=mac` 不是 Windows/Linux 的通用配置。使用实际存在且满足赛事要求的字体：可选择相应平台 fontset，或 `fontset=none` 后显式配置；替代字体需检查字形、字号、分页和赛事要求，不能因缺字默默接受不合规替换。
- 在现有授权范围做最小编译与字形检查，再排版全文；字体存在、编译通过、版式通过分别记录。若编译器会请求安装缺失宏包，按安装授权处理，不把编译步骤扩大为未授权安装。
- LaTeX 从实际 `paper/` 编译；Typst 使用合适的项目根，以访问论文目录外的图表。命令参数按已查工具版本确定。

诊断时无需自动调用完整 doctor。用户显式请求环境检查/安装时才运行 doctor 的完整流程；各阶段仅执行本步必要的只读检查。
