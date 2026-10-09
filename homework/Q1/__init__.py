# -*- coding: utf-8 -*-
#免责声明
# Source reference: SENTRY-REF-20261008-E55343F2C79D
# The provenance block at the end provides an optional integrity check.
# This reference must not be presented as independently authored work.
# An unsigned fingerprint is a comparison aid, not proof of authorship.
# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
import json


#安全转化整数
def _as_int(value, default=0):
    try:
        return int(value)
    #异常：
    # TypeError：当传入的值为 None 或其他非数字类型时，会引发 TypeError 异常。
    # ValueError：当传入的值无法转换为整数时，会引发 ValueError 异常。
    # OverflowError：当传入的值超出整数类型的表示范围时，会引发 OverflowError 异常。
    except (TypeError, ValueError, OverflowError):
        return default

    
# 血量百分比，返回 0-100 的 int
def hp_ratio(hp, max_hp):
    hp = _as_int(hp)
    max_hp = _as_int(max_hp)
    if max_hp <= 0:
        return 0
    return max(0, min(hp, max_hp)) * 100 // max_hp


#状态报告
def status_report(name, robot_type, hp, max_hp, battery):
    battery = max(0, min(100, _as_int(battery)))
    if battery >= 60:
        level = "OK"
    elif battery >= 20:
        level = "WARNING"
    else:
        level = "LOW"

    #注意排版
    return ("{:<10}|{:^10}|HP {:>3}%|BAT {:>3}%|{}".format(
        name, robot_type, hp_ratio(hp, max_hp), battery, level))
#版本溯源免责声明，仅供学习与参考
# === BEGIN SOURCE PROVENANCE v1 ===
# This block is deliberately separate from the implementation fingerprint.
# Verification is opt-in: importing and using the module behaves as before.