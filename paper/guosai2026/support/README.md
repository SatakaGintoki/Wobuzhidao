# 支撑材料使用说明

## 当前附录的精简求解程序

论文附录D现引用code/Q1.py至Q4.py，每问独立计算，仅需NumPy、SciPy、openpyxl。运行`python code/Q1.py`（其他问同理），原始附件和模板位于code/data/，新结果写入code/results/。论文同级的“支撑材料_按问复现”文件夹及压缩包提供同样的四个独立脚本和附件。

四份精简程序已通过语法导入、核心方程对照、短时积分和Excel抽样导出检查，未完整重算全部结果。以下为原始完整求解、验证及补充实验程序的历史说明，不代表精简版仍依赖Matplotlib、Node或其他问题的结果。

本文计算使用 Python、NumPy、SciPy、openpyxl 与 Matplotlib。原生产环境记录为 Python 3.14.6、NumPy 2.5.1、SciPy 1.18.0；程序相对项目根读取文件。Excel 3、4 的原导出脚本另需 Node.js 与 @oai/artifact-tool；已包含正式结果文件。

## 输入位置

把赛题原始附件置于 data/附件/附件1.xlsx、data/附件/附件2.xlsx、data/附件/附件3/result1.xlsx 至 result4.xlsx。原题数据按官方要求不重复放入支撑材料压缩包。

## 复算数值

先安装 requirements.txt 中依赖，在本目录运行：

```text
python code/problem1.py
python code/problem2.py
python code/problem3.py --no-xlsx
python code/problem4.py --level 2
python code/problem4.py --level 4
python code/problem4.py --level 4 --tight
python code/problem4.py --level 8
python code/problem4.py --level 16
python code/problem4.py --level 8 --tight
python code/verify_q4_results.py
python code/plot_q3_results.py
python code/plot_q4_radius.py
```

上述过程重新计算四问及所用加密对照并生成NPZ/CSV/图；第3问 --no-xlsx 不重新导出Excel，现有随附结果表保留。第1、2问脚本会覆盖本支撑目录下对应结果，建议在副本中复算。各类目录由程序建立，必要时预先创建 results、figures、reports、tmp。

## 原Excel 3、4导出路径

第3问完整导出需要预先配置 Node.js 和 @oai/artifact-tool 并运行不带 --no-xlsx 的 problem3.py；第4问数值核验完成后执行 node tmp/q4_export/build.mjs。Node 模块须能从两个脚本目录解析。若只需复核方程、NPZ和CSV，则不依赖Node。第3问导入随附result3.xlsx作为原布局。

## 程序附录与变更范围

code/ 包含全文模型、计算与对应验证程序；tmp/ 包含原Excel导出/门禁脚本。附录逐字载入源程序。仅把原计算机的Node绝对路径改为从PATH查找，并把第三问历史Excel模板路径改为随附结果表路径；未改物性、方程、积分容差、网格或数值流程。哈希映射见source_manifest.json。

较大的NPZ与网格诊断数组可按上述指令重建，不放入20MB以内的支撑材料包。报告中历史工作区归档路径是既有验证的来源记录，不表示本压缩包已包含全部历史备份。部分历史回归脚本需先生成完整诊断目录再运行。

## 2026-09-13 第三问二维端面校核

新增 q3_axisymmetric.py、verify_q3_axisymmetric.py、plot_q3_axisymmetric.py。results/q3_axisymmetric/附全部小型NPZ场、同网格配对CSV和验证JSON，完整重算命令见 reports/Q3_AXISYMMETRIC_REPORT.md 与论文程序附录。准备原附件1后，可直接运行验证程序并重绘，无须重新积分。额外依赖threadpoolctl用于限制线性代数线程。

运行原始记录中的路径已在算例JSON内改为相对路径，original_source_sha256保留原代码哈希；source_sha256对应随附代码，原problem3.py的导出路径适配沿用source_manifest.json说明。数值数组未改，详见packaging.json。原figure_provenance.json是生成记录；在本目录重新绘图后会生成当前目录的图源记录。该校核只支持第三问指定情景下的径向简化，不验证第四问收缩时长。

现有敏感性表的程序 q3_sensitivity.py 及全部情景JSON/CSV一并收录。其后期温度、水分量仅在4 h后改变，传质系数在全过程缩放；大数组可复算。

问题二的 $G_4/G_8$ 数值核验可运行：

```text
python code/verify_q2_results.py --numerical
```

该命令生成 `results/verification/q2/numerical_audit.json`，其中保留当次源数组哈希快照；随附 NPZ 的字段级数值与复核输出逐点一致，文件哈希差异只反映封装版本不同。

## AI记录

AI工具使用详情.pdf记录本次可确认的工具、用途与核验边界；历史工具版本及人工逐项核验须由参赛队据实补全，不能把自动检查等同于人工审阅。

## 2026-09-12 同物性收缩对照补充

新增code/q4_fixed_comparison.py和plot_q4_fixed_comparison.py。依次运行前者 --level 8、--level 16、--level 8 --tight、--summarize，最后运行绘图脚本。汇总前需已生成原q4_solution.npz和q4_validation.json；仅重绘可直接读取附带的results/q4_fixed_comparison/两份CSV及comparison.json，不必重算PDE。新增固定组不读取实测半径作为演化输入，不外推半径；后4小时沿用50°C、0.05kg/kg环境。详见reports/Q4_FIXED_COMPARISON_REPORT.md。
