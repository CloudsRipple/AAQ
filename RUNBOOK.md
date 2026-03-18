# Runbook（运行手册）

更新时间：2026-03-15

## 1. 网关断连（ALERT_GATEWAY_DISCONNECT）
1) 先执行 `phase0-ibkr-paper-check` 确认端口与会话状态。  
2) 若端口不通，检查 TWS/Gateway 进程与网络 ACL。  
3) 执行重连后再次触发 `phase0-ibkr-execute --send` 验证。  
4) 若持续失败，维持 `DEGRADED` 并禁止新开仓。

## 2. 重复下单风险（ALERT_DUPLICATE_ORDER_RISK）
1) 查询执行返回中 `deduplicated` 条目与对应 idempotency_key。  
2) 核查消息源是否重复投递或重放。  
3) 若重复频繁，提升上游去重并缩短重放窗口。  
4) 保持幂等防重开启，不允许临时关闭。

## 3. 异常回撤（ALERT_ABNORMAL_DRAWDOWN）
1) 读取 `drawdown_pct` 与阈值比值。  
2) 触发减仓策略并暂停新增风险暴露。  
3) 检查最近成交质量（滑点、拒单、延迟）。  
4) 若超过最大回撤阈值，执行 Kill Switch 并进入 `HALTED`。

## 4. 数据断流/脏数据（ALERT_DATA_OUTAGE）
1) 检查 `data_quality_gate.blocked_reasons`。  
2) 验证主源与备源连通性。  
3) 确认恢复后 `allow_trading=true` 再恢复开仓。  
4) 恢复前仅允许减仓，不允许新开仓。

## 5. 每日健康报告
1) 自动模式：运行 `phase0-health` 后自动生成日报。  
2) 手动模式：执行 `phase0-daily-health-report`。  
3) 报告位置：`artifacts/daily_health_report.latest.json|md`。  
4) 运营复盘重点：成功率、拒单率、P95延迟、滑点、回撤、风险拒绝率、告警总数。
