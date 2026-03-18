# 告警规则表

更新时间：2026-03-15

| Rule ID | 告警名称 | 触发条件 | 级别 | 动作 |
|---|---|---|---|---|
| ALERT_GATEWAY_DISCONNECT | 网关断连/执行链异常 | system_state 为 `DEGRADED/HALTED` 且 reason 包含 `RECONCILE` 或 `PARTIAL_EXECUTION_FAILURE` | critical | 记录告警、建议立即执行连通性检查与重连 |
| ALERT_DUPLICATE_ORDER_RISK | 重复下单风险 | 执行结果存在 `deduplicated=true` | warning | 记录告警、检查上游消息幂等来源 |
| ALERT_ABNORMAL_DRAWDOWN | 异常回撤 | `drawdown_pct >= 0.8 * max_drawdown` | warning/critical | 记录告警、触发仓位收缩与风险复核 |
| ALERT_DATA_OUTAGE | 数据断流/质量退化 | `data_quality_gate.degraded=true` | critical | 记录告警、阻断新开仓、排查主备数据源 |

## 执行说明
- 告警统一由 `evaluate_alerts` 评估并落盘至 `observability_alerts`。
- 所有告警都会输出 JSON 结构化日志事件 `alert_triggered`。
