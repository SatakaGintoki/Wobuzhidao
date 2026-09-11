"""Record the completed Q1/Q2 technical closeout without inventing user acceptance."""
from pathlib import Path
import json
import shutil

ROOT=Path(__file__).resolve().parents[1]
read=lambda p: json.loads((ROOT/p).read_text(encoding='utf-8'))
v={q:read(f'results/q{q}_validation.json') for q in (1,2)}
audit=read('results/verification/closeout/files.json')
gate=read('results/verification/closeout/gate_test.json')
assert all(x['delivery_gate']['meets_delivery_gate'] for x in v.values())
assert all(f['all_workbook_values_types_formats_unchanged'] for a in audit.values() for f in a['fields'].values())

def append(path, text):
    p=ROOT/path
    p.write_text(p.read_text(encoding='utf-8').rstrip()+'\n\n'+text.strip()+'\n',encoding='utf-8')

def prepend(path, text):
    p=ROOT/path
    p.write_text(text.strip()+'\n\n'+p.read_text(encoding='utf-8'),encoding='utf-8')

archive=ROOT/'reports/archive/pre-closeout-20260911'
archive.mkdir(parents=True,exist_ok=True)
for name in ['reports/STATE.md','reports/PAPER_NOTES.md','todo.md','plan.md']:
    dest=archive/Path(name).name
    if dest.exists(): raise RuntimeError('Do not overwrite historical snapshot: '+str(dest))
    shutil.copy2(ROOT/name,dest)

report='''# 前两问收尾报告

日期：2026-09-11。用户要求：“你帮我收尾一下并告诉我做了什么”。

## 结论与范围

前两问的代码修复、完整时段复算、结果一致性和前两问章节草稿已完成。交付版本为 `q1-closeout-v1`、`q2-closeout-v1`。
技术检查在既定一维、无显式潜热的等效模型及所列数值标准下通过；四位显示全部冻结、真实药材物理验证和全篇提交验收不在该PASS结论内。
当前执行授权包括所请求的两问收尾与可审阅章节整理；没有把用户的工作指令另记成对计算后新版本的结果采纳。采纳状态保留PENDING，第三、四问未运行。

## 做了什么

1. `code/delivery.py`统一组织必要检查；先存诊断，失败抛错，在全部正式NPZ、Excel、CSV、图形写入之前阻断。第一问补入此前遗漏的全输出网格差阈值。两问检查全部内部节点有限性、温湿上下界，水分下界改为题给环境最小值并容许1e-8数值偏差。
2. `code/q1_analytic.py`增加解析级数加倍检查；模态ODE提供准确稀疏对角Jacobian，避免大量模态使用稠密数值Jacobian。第一问温度最终用960项，水分对照两问均用640项；每次正式运行都重新检查参考收敛，不只是改变一个固定项数。
3. 第一问热湿收支改用连续解及PCHIP区间的自适应通量积分。原来的整秒梯形积分不足以满足方案写定的1e-6湿收支目标，现已解决，不放宽该目标。
4. 第二问温度剖面图将图例移到坐标框上方；两问NPZ补存初值及内部场检查点，第二问明确保存21点输出半径，避免与1057点内部网格混配。
5. 保留原模型、原生产空间网格和时间积分参数，从原始附件完整重算。前两问共529200个温度/含水率输出数值与收尾前一致，Excel全部数值、类型及数字格式不变；论文130个四位数值不变。
6. 将前两问写成LaTeX章节，含方程、边界、求解、表1--4、四张结果图、数值检验及局限。沿用已有国赛模板，提供单独前两问预览，后两问未填造结果。
7. 整理当前状态和待办，将混杂旧状态的记录保存到历史目录；更新结果报告、模型记录、论文来源映射。

## 数值证据

| 检查 | 第一问 | 第二问 |
|---|---:|---:|
| 计算时长/s | 1800 | 10800 |
| 生产内部节点 | 2113 | 1057 |
| 全量输出数值 | 75600 | 453600 |
| 相对原NPZ最大变化 | 0 | 0 |
| 论文表四位变化 | 0/70 | 0/60 |
'''
for label,key in [('时间加密温度最大差','T'),('时间加密含水率最大差','C')]:
    report+=f'| {label} | {v[1]["time_sensitivity"][key]["max_abs"]:.3e} | {v[2]["time_sensitivity"][key]["max_abs"]:.3e} |\n'
for label,field in [('热收支相对残差','T'),('湿收支相对残差','C')]:
    report+=f'| {label} | {v[1][f"conservation_{field}_1800s"]["relative_residual"]:.3e} | {v[2][f"conservation_{field}_10800s"]["relative_residual"]:.3e} |\n'
report+=f'''| 冻结D参考最大差 | {v[1]['frozen_D_moisture_vs_analytic']['max_abs']:.3e} | {v[2]['frozen_D_moisture_vs_analytic']['max_abs']:.3e} |
| 逐项失败注入阻断 | {gate['q1']['failure_cases_blocked']}项通过 | {gate['q2']['failure_cases_blocked']}项通过 |

第一问G4→G8：T差5.895e-7、C差4.564e-6，论文表全部稳定。第二问本轮G2→G4：T差2.452e-6、C差1.493e-5；此前独立G4→G8完整审核的差分别为6.244e-7、3.732e-6。本次核验原生产场完全相同，故保留已有G8审核证据，无须仅为归档与图例修改再次重复同一G8实验。

第一问在加密网格对比中仍有温度79格、含水率73格四位显示变化；其时间加密有2个温度单元格末位变化。第二问已有G4→G8审核同样存在少量四位末位翻转。适用结论是“全输出点相邻网格差达到2e-5目标，论文表四位稳定”，不能写成全部Excel第四位已冻结，也不能把网格差称为严格真误差上界。

第一问首次收尾运行在温度参考120→240→480项仍未达1e-8时失败，实际退出非零；11个原正式结果文件SHA256全部不变。保留 `q1_blocked_reference.json` 和 `blocked_run_preserved_files.json` 作为真实阻断证据。随后加倍至960项通过，未放宽截断阈值。
独立首秒PCHIP解析卷积与640项模态ODE最大差约1e-14，640→1280项差约1e-11，见 `modal.json`。

## 文件、来源与复现

- 答卷：`results/result1.xlsx`、`results/result2.xlsx`。
- 未舍入源解及验证：`results/q1_solution.npz`、`results/q2_solution.npz`、对应`q1_validation.json`、`q2_validation.json`。
- 归档：`results/archive/pre-closeout-20260911/manifest.json`及原文件快照；原第一问v1仍保留在其原归档中。
- 当前综合核验：`code/verify_closeout.py`；`results/verification/closeout/files.json`、`gate_test.json`、`modal.json`及图页渲染。
- 第一问原`code/verify_q1_results.py`是均匀网格v1历史审核脚本；新版非均匀网格验收使用`verify_closeout.py`，不会将旧脚本证据混为本次通过依据。
- 完整生产复现：`D:/python/python.exe code/problem1.py`，再运行`D:/python/python.exe code/problem2.py`。
- 门禁测试/解析独立核查：同一数值解释器运行`code/verify_closeout.py --gate`和`--modal`。
- 文件/PDF核查：宿主捆绑Python运行`code/verify_closeout.py`和`--render`；不需要重跑PDE。
- 日志：`tmp/q1_closeout_run.log`、`tmp/q2_closeout_run.log`。
- LaTeX章节：`paper/closeout/sections/5_problem1.tex`、`6_problem2.tex`；单独预览`paper/q12_closeout.tex`/`.pdf`；整篇入口仍是`paper/main.tex`。
- 文献复用已全文核实的L02，仅支持圆柱导热/扩散方法旁证；物性来自题面，参考解及收支关系为本题推导，不为这些结果编造新引用。

## 仍保留的范围限制

结果是所选等效模型下的模拟；空气/固体干基转换未独立标定，无显式潜热，端面效应未做二维验证。制造解、解析对照和收支检查只能支持数值实现，不能证明这些物理简化对真实样品误差很小。
Excel本轮全量核对数值、类型、格式和网格，显示视图与原文件相同；未启动原生Excel。全篇仍有第三、四问及摘要等未完成内容，不能把前两问章节预览或主文档可编译说成全文可提交。
'''
(ROOT/'reports/Q12_CLOSEOUT_REPORT.md').write_text(report,encoding='utf-8')

state='''# 当前状态索引

## 2026-09-11：前两问技术收尾完成

- 用户授权：“你帮我收尾一下并告诉我做了什么”，执行范围为前两问修复、复算、核验、章节草稿及状态整理。
- 当前交付：`q1-closeout-v1`、`q2-closeout-v1`；技术核验PASS（已选等效模型与明确数值阈值下），结果采纳PENDING，不自动登记用户已批准新版本。
- 前两问所有答卷数值与收尾前一致。修复发布门禁、参考级数收敛、第一问通量积分、第二问图例和内部场归档。
- 入口：`reports/Q12_CLOSEOUT_REPORT.md`；证据`results/verification/closeout/`；Excel位于`results/result1.xlsx`与`result2.xlsx`。
- 论文采用已选LaTeX/xelatex；前两问已积累到`paper/closeout/sections/5_problem1.tex`、`6_problem2.tex`，单独预览`paper/q12_closeout.pdf`。全文仍未完成。
- 第一问旧v1、v2及第二问旧v1为历史版本；数值未失效，当前代码及验证以closeout版本为准。原快照及SHA256见`results/archive/pre-closeout-20260911/`。
- 第三问：`q3-discussion-v1`，后期环境和实施方案未定，创新选型暂缓；无求解结果。
- 第四问：`q4-discussion-v1`，收缩运动与经验密度解释未闭合；无求解结果。
- 下一步：审阅前两问交付，随后明确第三问实施方案。本轮没有开启第三、四问求解。

## 偏好、模型与历史入口

- 只做A题《药材的烘干问题》，四问，中文国赛论文；整体路线`A-route-v1`已批准。
- 已批准第一问方案`q1-plan-v1`及PCHIP修订；第二问`q2-plan-v2`，PCHIP、一维、不做二维或潜热探索。
- 第二问从原初值独立计算，不使用第一问末态；第三问不能从已舍入Excel恢复内部状态。
- 方案详情：`reports/models/q1.md`至`q4.md`；决定原文：`reports/REVIEW_LOG.md`。
- 文献：`reports/LITERATURE_REPORT.md`；论文来源：`reports/PAPER_NOTES.md`；图形风格：`figures/STYLE.md`。
- 完整旧状态记录保存在`reports/archive/pre-closeout-20260911/STATE.md`，其中旧“当前”标签均为历史时点。
'''
(ROOT/'reports/STATE.md').write_text(state,encoding='utf-8')
(ROOT/'todo.md').write_text('''# 当前待办

## 前两问收尾

- [x] 保留原结果快照和SHA256
- [x] 修复正式导出前的失败阻断，补齐必需验证项
- [x] 解析参考级数加倍与首秒独立卷积核查
- [x] 第一问连续解自适应通量积分及新版复算
- [x] 第二问图例调整、内部场与初值归档及完整复算
- [x] Excel、NPZ、CSV、检查点全量一致性和门禁失败测试
- [x] 前两问LaTeX章节草稿与可视化预览
- [x] 更新模型、结果、状态和来源映射
- [ ] 用户审阅当前前两问交付版本

## 后续

- [ ] 明确第三问4小时后环境延续和求解方案，完成基线及达标时间验证
- [ ] 明确第四问收缩运动与密度闭合，完成基线
- [ ] 根据具体不足决定是否开展有限改进实验
- [ ] 全文整合、摘要、模型评价、最终格式与提交检查

历史待办保存在`reports/archive/pre-closeout-20260911/todo.md`，不能据旧条目启动已过期任务。
''',encoding='utf-8')
notes='''# 论文笔记与来源映射

- 引擎沿用用户已选LaTeX/xelatex；入口`paper/main.tex`；编译器`D:/MikTex/miktex/bin/x64/xelatex.exe`。主论文正有并行编辑，本轮最终交付位于独立closeout目录，避免覆盖。
- 前两问收尾授权包含可审阅章节整理；章节为草稿，结果采纳状态仍PENDING。本轮不写摘要和后问结果。
- 第一问章节`paper/closeout/sections/5_problem1.tex`：对应q1-plan-v1/PCHIP和q1-closeout-v1；表1、2来自`results/q1_solution.npz`，验证来自`q1_validation.json`；径向温湿图来自`figures/q1_T_profiles.pdf`、`q1_C_profiles.pdf`。
- 第二问章节`paper/closeout/sections/6_problem2.tex`：对应q2-plan-v2和q2-closeout-v1；表3、4来自`results/q2_solution.npz`，验证来自`q2_validation.json`及已有独立G8审核；图来自`figures/q2_T_profiles.pdf`、`q2_C_profiles.pdf`。
- 章节构建脚本`code/build_q12_chapters.py`，表格直接从未舍入NPZ格式化四位小数，避免CSV二次舍入。参考文献hussain2003对应文献记录L02，只引方法旁证。
- 独立阅读入口`paper/q12_closeout.pdf`，源文件复用主模板前导及相同章节；整篇仍有未完成占位，不是提交版。
- 符号统一：T以摄氏度存储；Arrhenius项使用T+273.15；C为kg水/kg干物质；R=0.02m；B=rho*cp为有效体积热容量。
- 第一问温度/水分分别积分；第二问两场联合积分且物性全时段替换为附录3，均从原初值开始，不拼接两问结果。
- 结果中全部规定输出点通过2e-5相邻网格差目标，论文表四位稳定；不得写“全部Excel末位完全冻结”“真实物理预测精度达到四位”。
- 第一问湿收支旧2.10e-6来自1s梯形积分，本次改为连续解自适应积分；解析对照截断检查也已更新，旧验证描述须结合收尾报告阅读。
- `paper/drafts/`原始推导保留为历史写作材料；本轮最新章节与数值以本映射为准。历史笔记保存在`reports/archive/pre-closeout-20260911/PAPER_NOTES.md`。
'''
previous_notes=(ROOT/'reports/PAPER_NOTES.md').read_text(encoding='utf-8')
(ROOT/'reports/PAPER_NOTES.md').write_text(notes+'\n## 其他写作任务记录（原文保留，数值版本以上方收尾映射为准）\n\n'+previous_notes,encoding='utf-8')
append('reports/REVIEW_LOG.md','''## 2026-09-11：前两问集中收尾 q12-closeout-task

- 用户原话：“你帮我收尾一下并告诉我做了什么”。状态APPROVED指本轮修复、复算、验收材料与章节草稿整理的执行授权。
- 已完成：q1-closeout-v1、q2-closeout-v1，详见reports/Q12_CLOSEOUT_REPORT.md；数值技术检查PASS，所有原答卷数字保持一致。
- 本轮不变更物理模型或后问范围，不将工作授权填作用户对新交付版本的事后采纳。结果采纳PENDING，前两问章节为可审阅草稿。
- 验证标准：相邻全输出网格差2e-5、论文表四位稳定、内部界限/有限性、参考截断1e-8、离散收支1e-6；全部Excel末位完全冻结并未实现，明确列为范围限制。
''')
prepend('reports/RESULTS_REPORT.md','''> **2026-09-11收尾更新（优先于下方历史描述）**：当前版本q1-closeout-v1、q2-closeout-v1。正式数值与原q1-baseline-v2/q2-baseline-v1完全一致，下方表格继续有效；代码已修复失败导出、解析截断检查、第一问收支积分，补齐检查点并调整第二问图例。新验证值及状态见`Q12_CLOSEOUT_REPORT.md`和`results/q1_validation.json`、`q2_validation.json`。下方旧“早期解析差来自初边值不相容”“导出门禁待修”等描述属于历史记录，不是当前结论。\n''')
for q in (1,2):
    prepend(f'reports/models/q{q}.md',f'''> **2026-09-11收尾更新**：当前交付q{q}-closeout-v1，原物理方案与答卷数值保持不变，技术核验PASS（所列数值标准），结果采纳PENDING。新增正式写出前的失败阻断、参考截断收敛及内部场检查点；第一问另修正通量积分，第二问另调整图例。验收入口`reports/Q12_CLOSEOUT_REPORT.md`，论文段落`paper/closeout/sections/{5 if q==1 else 6}_problem{q}.tex`。下文旧“未求解/待修”按历史时点阅读。
''')
prepend('reports/Q2_VERIFY_REPORT.md','> 2026-09-11后续修复：本报告列出的四项问题已在q2-closeout-v1中修复并核验，当前报告见`Q12_CLOSEOUT_REPORT.md`。本文保留原审核证据，原FAIL不作为当前交付状态。')
prepend('reports/VERIFY_REPORT.md','> 2026-09-11版本说明：本文为第一问均匀网格旧版审核。当前q1-closeout-v1已完成PCHIP加密复算及技术收尾，见`Q12_CLOSEOUT_REPORT.md`。勿以本旧版结论判断当前结果。')
prepend('plan.md','''> **当前执行状态（2026-09-11）**：前两问收尾完成，当前交付q1-closeout-v1、q2-closeout-v1，技术核验及章节草稿见`reports/Q12_CLOSEOUT_REPORT.md`。排版沿用已选LaTeX/xelatex。下方早期“尚未求解”等句为历史记录，当前进度以`reports/STATE.md`为准；原plan快照已保存到`reports/archive/pre-closeout-20260911/plan.md`。''')
print('Recorded closeout and preserved historical state.')
