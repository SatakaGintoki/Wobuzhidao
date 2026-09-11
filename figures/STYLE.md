# 绘图风格

状态：初稿建议，尚未由用户定为全文风格。

- 字体：Microsoft YaHei / SimHei，图内 8–10 pt
- 图内不放总标题；坐标含符号与单位
- 线宽约 1.2，多曲线用颜色区分，必要时线型辅助
- 导出：PDF，`fonttype=42`
- 第1问初稿：`q1_oven_input.pdf`，`q1_T_profiles.pdf`，`q1_C_profiles.pdf`，`q1_T_center_surface.pdf`，`q1_C_center_surface.pdf`
- 第3问初稿：`q3_C_max_history.pdf`，`q3_C_profiles.pdf`，`q3_max_location.pdf`，`q3_event_zoom.pdf`，`q3_T_center_surface.pdf`
- 第4问初稿：q4_C_history.pdf、q4_C_profiles.pdf；沿用中文字体与现有风格，实际物理距离横轴，数据源results/q4_solution.npz，已视觉检查。

## 第三问收尾图形增量（2026-09-11）

q3-closeout-v1沿用原字体和配色。剖面图图例置于坐标轴上方、三列排布以免遮线；事件图横轴采用相对临界时刻的秒数，显示临界前90 s附近的保存状态、临界根及严格报告时刻。两条时间标注显示六位小时，保存点间连线仅为视觉引导。复现code/plot_q3_results.py，来源results/diagnostics/q3_delivery/figure_provenance.json。本条为第三问局部修复，不代表用户选择了全文统一新风格。
