# Capacity alignment reconciliation

The capacity controls reconciled on main at revision `a8c5829f56ca525cc4c40b2fb339c8fb05a8d0b1` remain part of framework 1.6 / protocol 2.4.

The static `.interagent/capacity/freshness_policy.json` is a deployable control input and is therefore included by the package dependency map. The volatile `.interagent/capacity/current.json` signal remains project runtime state and is intentionally excluded from deployment packages. The `EXHAUSTED` boundary coverage in `tests/test_capacity.py` is preserved.
