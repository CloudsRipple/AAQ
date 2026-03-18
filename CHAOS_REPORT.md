# Chaos 测试报告

执行时间：2026-03-15

## 1. 测试范围
- 断网
- 延迟
- 脏数据
- 重启
- 数据库锁冲突

## 2. 测试命令
- `.venv/bin/python -m unittest discover -s tests -p 'test_chaos_resilience.py' -v`
- `.venv/bin/python -m phase0.replay --mode all`

## 3. 结果汇总

### 3.1 Chaos 单测
- `test_db_lock_conflict_degrades_data_gate`：通过
- `test_latency_and_dirty_data_block_trading`：通过
- `test_network_disconnect_retry_then_success`：通过
- `test_restart_dedup_prevents_duplicate_submit`：通过
- 汇总：`4 passed, 0 failed`

### 3.2 Replay 稳定性
- 场景：5 个
  - breaking_news
  - high_volatility
  - duplicate_event_dedup
  - unverified_stale_message
  - safety_mode_blocked
- 汇总：`5 passed, 0 failed`

## 4. 关键观测
- 断网场景可通过指数退避重试恢复，避免瞬时抖动导致漏单。
- 延迟与脏数据被数据门禁阻断，不会继续开仓。
- 重启场景幂等键生效，避免重复下单。
- DB 锁冲突触发降级与交易阻断，避免脏状态继续传播。
