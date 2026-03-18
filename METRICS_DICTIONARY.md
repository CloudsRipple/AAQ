# 指标字典

更新时间：2026-03-15

| 指标名 | 含义 | 公式/口径 | 数据来源 | 刷新频率 |
|---|---|---|---|---|
| order_success_rate | 下单成功率 | `ok executions / total attempts` | execution_reports | 每执行周期 |
| order_reject_rate | 拒单率 | `rejected executions / total attempts` | execution_reports + lifecycle | 每执行周期 |
| p95_latency_ms | 执行延迟P95 | 提交耗时样本 P95 | execution_reports.latency_ms | 每执行周期 |
| avg_slippage_bps | 平均滑点 | `mean(slippage_bps)` | execution_quality | 每执行周期 |
| drawdown_pct | 当前回撤 | 运行态回撤值 | trading_runtime.drawdown | 每执行周期 |
| risk_reject_rate | 风控拒绝率 | `risk_rejected / risk_total` | risk_decision_outcome | 每执行周期 |
| risk_decisions_total | 风控总裁决数 | `count(APPROVED+REJECTED)` | risk_decision_outcome | 每执行周期 |
| alerts_today | 当日告警数 | 最近窗口告警计数 | observability_alerts | 每日报告 |

## 口径注意事项
- `order_success_rate` 与 `order_reject_rate` 默认不计入 dry-run。
- `slippage_bps` 方向归一后记录（买单正滑点为不利）。
- `p95_latency_ms` 样本不足时按现有样本计算。
