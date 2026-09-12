# 支撑材料使用说明

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
```

上述过程重新计算四问及所用加密对照并生成NPZ/CSV/图；第3问 --no-xlsx 不重新导出Excel，现有随附结果表保留。第1、2问脚本会覆盖本支撑目录下对应结果，建议在副本中复算。各类目录由程序建立，必要时预先创建 results、figures、reports、tmp。

## 原Excel 3、4导出路径

第3问完整导出需要预先配置 Node.js 和 @oai/artifact-tool 并运行不带 --no-xlsx 的 problem3.py；第4问数值核验完成后执行 node tmp/q4_export/build.mjs。Node 模块须能从两个脚本目录解析。若只需复核方程、NPZ和CSV，则不依赖Node。第3问导入随附result3.xlsx作为原布局。

## 程序附录与变更范围

code/ 包含全文模型、计算与对应验证所用18个完整Python文件；tmp/ 包含4个原Excel导出/门禁脚本。附录逐字载入这些文件。仅把原计算机的Node绝对路径改为从PATH查找，并把第三问历史Excel模板路径改为随附结果表路径；未改物性、方程、积分容差、网格或数值流程。哈希映射见source_manifest.json。

较大的NPZ与网格诊断数组可按上述指令重建，不放入20MB以内的支撑材料包。报告中历史工作区归档路径是既有验证的来源记录，不表示本压缩包已包含全部历史备份。部分历史回归脚本需先生成完整诊断目录再运行。

## AI记录

AI工具使用详情.pdf记录本次可确认的工具、用途与核验边界；历史工具版本及人工逐项核验须由参赛队据实补全，不能把自动检查等同于人工审阅。
