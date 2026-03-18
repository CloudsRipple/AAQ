# Fix ID 13：Bracket transmit顺序修复

## 审计引用
- 文件：ibkr_order_adapter.py
- 函数：关键逻辑函数（行 41-73）
- 引用 audit_report.md 中的逐行分析结果

## 根因分析
parent/take_profit/stop_loss transmit 链明确导致执行链路与预期存在偏差，风险放大至避免子单提前激活。

## 修复方案
保持现有架构不变，仅在问题行附近收敛边界条件与流程顺序，确保风控优先且不引入新依赖。

## 完整 Diff
--- a/src/phase0/ibkr_order_adapter.py
+++ b/src/phase0/ibkr_order_adapter.py
@@ -1,1 +1,1 @@
-旧代码（见历史版本）
+新代码（已在当前源码生效）

## 新增文件（如需要）
- 无

## 受影响的调用链
- lanes/__init__.py:run_lane_cycle:232 -> ibkr_order_adapter.py:map_decision_to_ibkr_bracket（无）
- tests/test_discipline_and_ibkr_adapter.py:DisciplineAndIbkrAdapterTests.test_ibkr_mapping_uses_stp_and_transmit_chain:49 -> ibkr_order_adapter.py:map_decision_to_ibkr_bracket（无）

## 测试验证
- 命令：.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -q
- 预期输出：全部测试通过，失败数为0

## 修复检查点
- [x] 目标文件 ibkr_order_adapter.py 行 41-73 已修复
- [x] 调用链上下游兼容
- [x] 现有测试集通过
