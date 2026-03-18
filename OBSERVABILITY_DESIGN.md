# Observability 设计文档

更新时间：2026-03-15

## 1. 目标
- 问题可发现：关键指标与告警覆盖数据、风控、执行、网关链路。
- 问题可定位：结构化日志统一 `event` + 上下文字段。
- 问题可复盘：生命周期事件、风控审计、成交质量、每日健康报告落盘。

## 2. 架构组件
- 日志层：`src/phase0/logger.py` + `src/phase0/observability.py:log_event`
- 指标层：`build_metrics_snapshot`
- 告警层：`evaluate_alerts`
- 报告层：`generate_daily_health_report`
- 存储层：`state_store` 中 `execution_reports / execution_quality / risk_decision_outcome / observability_alerts`

## 3. 数据流
1) 执行周期结束后，`execute_cycle` 汇总执行结果并计算指标。  
2) 同步评估告警规则，命中后写入 `observability_alerts`。  
3) 主程序运行结束自动产出 `artifacts/daily_health_report.latest.json|md`。  
4) 运营侧以日报 + 告警历史做日内与日终复盘。

## 4. 关键实现映射
- JSON 结构化日志：`src/phase0/logger.py`
- 指标聚合与 P95 统计：`src/phase0/observability.py`
- 告警触发与持久化：`src/phase0/observability.py` + `src/phase0/state_store.py`
- 日报生成：`src/phase0/observability.py` 与 `src/phase0/daily_health_report.py`

## 5. 运行方式
- 自动：`phase0-health` 结束后自动生成日报。
- 手动：`phase0-daily-health-report` 生成最新运营摘要。
