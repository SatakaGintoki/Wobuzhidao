---
name: doctor
description: "按当前建模、写作或验收阶段检查解释器、所需包和外部工具，定位已有环境；用户明确要求安装时再处理具体缺失项。用于显式环境诊断请求。"
allowed-tools: Bash(*), Read, Write
---

# 环境检查与安装向导

仅在用户显式请求环境检查或安装时运行完整诊断。各阶段可独立执行本步必要的只读检查，不为启动建模自动安装完整工具集。

先读取 [实际运行环境与路径](../_references/runtime_environment.md)，复用项目已记录的环境。默认不改变系统配置。

## 1. 确定本次阶段与解释器

从用户任务推断 modeling、writing 或 verification，以及已选排版引擎；没有到排版阶段，不要求先确定引擎。纯建议题没有计算需要时说明不适用。

Windows PowerShell 定位候选：

```powershell
Get-Command python,python3,py -ErrorAction SilentlyContinue | Select-Object Name,Source
# 如有 Python launcher，可用 py -0p 查看其登记的解释器。
```

Bash 定位候选：

```bash
command -v python3 || command -v python
```

选择项目已有解释器并记录绝对路径，不只记录模糊的 python/python3 别名。候选是否满足依赖由下面脚本实际导入核对；缺包先查另一个已知环境。

## 2. 运行只读检查

使用本 Skill 的 `scripts/check_environment.py`，下例变量均由实际发现的路径赋值。

```powershell
& $pythonExe $probeScript --phase modeling --require-package openpyxl
& $pythonExe $probeScript --phase writing --engine latex
& $pythonExe $probeScript --phase verification --engine latex
```

```bash
"$python_bin" "$probe_script" --phase modeling --require-package openpyxl
"$python_bin" "$probe_script" --phase verification --engine typst
```

按当前阶段选一条，不默认全跑。`--require-package` 使用实际 import 名称，可重复；只有输入/方法需要才加入。`--tool 名称=绝对路径` 用于登记已知但不在 PATH 中的工具；`--output` 可写入赛题的已有报告目录。

- modeling：检查 numpy/pandas/matplotlib；需要 Excel、优化等时增加 openpyxl/scipy。没有数值任务时跳过。
- writing：检查选定编译器，不要求安装另一套引擎。
- verification：检查选定编译器及可用 PDF 栅格化工具。已有等价能力时记录实际成功证据，不能只凭名称判失败或通过。

脚本退出码：0 表示所查依赖已发现，1 表示必需项缺失/导入失败，2 表示参数错误。`DETECTED` 仅代表包导入/命令路径，不证明字体、宏包、编译或视觉检查通过。

## 3. 解释缺口并处理

区分可以开始建模、可以排版、可以完成最终验收。报告解释器、包版本、命令路径、本步缺失项及未验证项。实际需要时再做最小编译、字体或 PDF 渲染检查。

如需要安装，先检查会话已有授权。用户已经明确要求安装具体缺失项时按范围执行；否则给出具体依赖、用途和安装范围再请求授权。安装命令从该工具当前官方文档核实，选择当前平台可用方式，不照搬过时包名或一律安装完整 TeX 发行版。Python 包通过已选解释器的 `-m pip` 安装。

安装或环境切换后重查受影响项；未经授权不自动安装系统软件、改变全局 PATH 或删除其他环境。将最终可用路径记入项目已有计划/运行报告，保持 STATE 的环境索引一致。
