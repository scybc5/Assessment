import json

def analyze_damage_log(lines):
    total = 0   #有效伤害总和
    by_armor = {"front": 0, "left": 0, "right": 0}  # 各部位有效伤害统计
    valid_count = 0 # 有效事件计数
    seen_ids = set()    # 用于去重的id集合

    #F->front, L->left, R->right
    sensor_map = {"F": "front", "L": "left", "R": "right"}

    for raw_line in lines:
        line = raw_line.strip()
        # 空行 / #注释 直接跳过
        if len(line) == 0 or line.startswith("#"):
            continue

        # ========== 尝试解析 JSON 行 ==========
        try:
            data = json.loads(line)
            # JSON行校验
            armor = data.get("armor")
            damage = data.get("damage")
            if armor not in ["front", "left", "right"]:
                continue
            if not isinstance(damage, int) or damage <= 0:
                continue

            json_id = data.get("id")
            # id去重逻辑
            if json_id is not None:
                if json_id in seen_ids:
                    continue
                seen_ids.add(json_id)

            # 统计
            by_armor[armor] += damage
            total += damage
            valid_count += 1
            continue
        except json.JSONDecodeError:
            # 不是JSON，继续尝试传感器行解析
            pass

        # ========== 尝试解析传感器行 F:32,L:5,R:12 ==========
        parts = line.split(",")
        sensor_valid = True
        sensor_sum = 0
        temp_add = {"front":0, "left":0, "right":0}

        for seg in parts:
            seg = seg.strip()
            if ":" not in seg:
                sensor_valid = False
                break
            key_str, val_str = seg.split(":", 1)
            key_str = key_str.strip()
            val_str = val_str.strip()
            if key_str not in sensor_map:
                sensor_valid = False
                break
            # 转正整数
            try:
                dmg = int(val_str)
            except ValueError:
                sensor_valid = False
                break
            if dmg <= 0:
                sensor_valid = False
                break
            armor_name = sensor_map[key_str]
            temp_add[armor_name] += dmg
            sensor_sum += dmg

        if not sensor_valid:
            # 传感器行任意一段非法 → 整行丢弃
            continue
        # 传感器行有效，计入统计
        for k in by_armor:
            by_armor[k] += temp_add[k]
        total += sensor_sum
        valid_count += 1

    # ========== 计算 avg 和 most_hit ==========
    if valid_count == 0:
        avg = 0.0
        most_hit = None
    else:
        avg = total / valid_count
        # 寻找伤害最高部位
        max_dmg = max(by_armor.values())
        most_hit = None
        # 按 front > left > right 顺序，遇到第一个最大值
        for name in ["front", "left", "right"]:
            if by_armor[name] == max_dmg:
                most_hit = name
                break

    result = {
        "total": total,
        "by_armor": by_armor,
        "most_hit": most_hit,
        "avg": avg
    }
    return result