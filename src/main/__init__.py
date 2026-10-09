# -*- coding: utf-8 -*-
#现在已有的注释不要删，这是免责声明！！！！！！！！！
# Source reference: SENTRY-REF-20261008-E55343F2C79D
# The provenance block at the end provides an optional integrity check.
# This reference must not be presented as independently authored work.
# An unsigned fingerprint is a comparison aid, not proof of authorship.
"""Sentry diagnostics, damage analysis, navigation, and patrol control.

Run ``python main.py`` for the supplied ASCII demonstration.
"""
import json
from collections import deque
from enum import Enum


# ---------------------------------------------------------------------------
# 仿真世界基础（已提供，勿改）
# ---------------------------------------------------------------------------
class Facing(Enum):
    """朝向枚举。世界坐标 (x, y)：x 向右增长，y 向上增长（数学系）。"""

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

   
    @property
    def delta(self):
        """该朝向的单位位移向量 (dx, dy)。"""
        return self.value[0], self.value[1]


# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
def hp_ratio(hp, max_hp):
    """Return a clamped integer percentage without floating-point rounding."""
    # _as_int 后来在后面补的，懒得把定义过程挪到前面了
    hp = _as_int(hp)
    max_hp = _as_int(max_hp)
    if max_hp <= 0:
        return 0
    return max(0, min(hp, max_hp)) * 100 // max_hp



def _as_int(value, default=0):
    """Normalize a numeric reading, falling back on invalid values."""
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return default


def status_report(name, robot_type, hp, max_hp, battery):
    """Format diagnostics using fixed field widths and battery thresholds."""

    
    battery = max(0, min(100, _as_int(battery)))
    if battery >= 60:
        level = "OK"
    elif battery >= 20:
        level = "WARNING"
    else:
        level = "LOW"

    
    return ("{:<10}|{:^10}|HP {:>3}%|BAT {:>3}%|{}".format(
        name, robot_type, hp_ratio(hp, max_hp), battery, level))


# ---------------------------------------------------------------------------
# Q2 战斗日志分析（题面 Q2·多源日志解析与统计）
# ---------------------------------------------------------------------------


def analyze_damage_log(lines):
    """Aggregate valid damage events, rejecting malformed lines atomically.

    Each sensor segment counts as one event. Ties use front, left, right
    order. Only valid JSON records reserve their IDs for deduplication.
    """
    by_armor = {"front": 0, "left": 0, "right": 0}
    seen_ids = set()  
    event_count = 0

    
    try:
        source = iter(lines)
    except TypeError:
        source = iter(())

    for line in source:

       
        if not isinstance(line, str):
            continue
        line = line.strip()

        
        if not line or line.startswith("#"):
            continue

        try:
            
            if line.startswith("{"):  
                record = json.loads(line)
                armor = record["armor"]
                damage = record["damage"]

                
                if armor not in by_armor or type(damage) is not int:
                    continue
                if damage <= 0:
                    continue

                
                if "id" in record:
                    event_id = record["id"]
                    if event_id in seen_ids:
                        continue
                    seen_ids.add(event_id)
                events = [(armor, damage)]

           
            else:
                events = _parse_sensor_damage(line)

        
        except (TypeError, ValueError, KeyError, RecursionError):
            continue

        
        for armor, damage in events:
            by_armor[armor] += damage
            event_count += 1

   
    total = sum(by_armor.values())

   
    try:
        average = round(total / event_count, 2) if event_count else 0.0
        
    except OverflowError:
        average = float("inf")

   
    return {
        "total": total,
        "by_armor": by_armor,
        "most_hit": max(by_armor, key=by_armor.get) if event_count else None,
        "avg": average,
    }




def _parse_sensor_damage(line):
    """Validate a complete sensor line before returning any events."""
    armor_names = {"F": "front", "L": "left", "R": "right"}  # codex预测的翻译表
    events = []
    for segment in line.split(","):

       
        armor, value = (part.strip() for part in segment.split(":"))
        if not value.isascii() or not value.isdecimal():
            raise ValueError("Damage must contain decimal digits")

        
        damage = int(value)
        if damage <= 0:
            raise ValueError("Damage must be positive")
        events.append((armor_names[armor], damage))
    return events


# ---------------------------------------------------------------------------
# Q3 SentryGrid（题面 Q3·载体物理规则）
# ---------------------------------------------------------------------------


class SentryGrid:
    """A grid vehicle with collision detection and finite movement fuel."""

    def __init__(self, width, height, obstacles, enemy_pos,
                 start_pos=(0, 0), facing=Facing.UP, fuel=100):

        self._width = int(width)
        self._height = int(height)
        if self._width <= 0 or self._height <= 0:
            raise ValueError("地图尺寸必须为正")

        
        self._obstacles = set()
        for ob in obstacles:
            x, y = ob
            self._obstacles.add((int(x), int(y)))
        if not isinstance(enemy_pos, (tuple, list)) or len(enemy_pos) != 2:
            raise TypeError("enemy_pos 需要长度为 2 的 tuple/list")
        self._enemy_pos = self._clamp_cell(enemy_pos)
        if self._enemy_pos in self._obstacles:
            raise ValueError("enemy_pos 不能位于障碍物上")
        if not isinstance(facing, Facing):
            facing = Facing.UP
        self._facing = facing
        self._fuel = int(fuel)
        self._collision_count = 0
        self.current_pos = start_pos

    def _clamp_cell(self, cell):
        """已提供：元素转 int 并夹回地图范围（供 __init__ 使用）。"""
        x = int(cell[0])
        y = int(cell[1])
        x = max(0, min(self._width - 1, x))
        y = max(0, min(self._height - 1, y))
        return (x, y)

    # -- 只读属性（已提供，勿改） ------------------------------------------
    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def enemy_pos(self):
        return self._enemy_pos

    @property
    def facing(self):
        return self._facing

    @property
    def fuel(self):
        return self._fuel

    @property
    def collision_count(self):
        return self._collision_count

    @property
    def obstacles(self):
        """障碍集合的只读视图（内部 set 引用，不要修改它）。"""
        return self._obstacles

    @property
    def found_enemy(self):
        return self._pos == self._enemy_pos

    def is_blocked(self, x, y):
        """已提供：坐标是否为障碍或越界（O(1)）。"""
        return ((x, y) in self._obstacles
                or not (0 <= x < self._width and 0 <= y < self._height))

    # -- 你要实现的部分 ------------------------------------------------------
    
    @property
    def current_pos(self):
        """当前位置 (x, y) 的 tuple。"""
        return self._pos

    @current_pos.setter
    def current_pos(self, value):
        """Convert and clamp a coordinate pair, rejecting obstacle cells."""

        
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise TypeError("Position must be a tuple or list of length two")

        position = self._clamp_cell(value)
        if position in self._obstacles:
            raise ValueError("Position cannot be on an obstacle")

        self._pos = position

    def move_forward(self):
        """Spend one fuel per powered attempt; walls leave position intact."""

        if self._fuel <= 0:
            return self._pos

        self._fuel -= 1
        dx, dy = self._facing.delta
        position = (self._pos[0] + dx, self._pos[1] + dy)

        
        if self.is_blocked(*position):
            self._collision_count += 1
        else:
            self._pos = position

        return self._pos

    def turn_left(self):
        """Rotate counterclockwise without consuming fuel."""

        dx, dy = self._facing.delta
        self._facing = Facing((-dy, dx))
        return self._facing

    def turn_right(self):
        """Rotate clockwise without consuming fuel."""

        dx, dy = self._facing.delta
        self._facing = Facing((dy, -dx))
        return self._facing


# ---------------------------------------------------------------------------
# Q4 贪心导航（题面 Q4·单步贪心导航策略）
# ---------------------------------------------------------------------------
def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
    """Choose a distance-reducing step, preferring the x axis on ties."""

    dx, dy = target[0] - pos[0], target[1] - pos[1]  

    horizontal = Facing.RIGHT if dx > 0 else Facing.LEFT 
    vertical = Facing.UP if dy > 0 else Facing.DOWN

    candidates = [(dx, horizontal), (dy, vertical)]

    if abs(dy) > abs(dx):  
        candidates.reverse()

    for difference, direction in candidates:  
        if difference == 0:
            continue

        step_x, step_y = direction.delta
        if (pos[0] + step_x, pos[1] + step_y) not in obstacles:
            return direction

    return current_facing


# ---------------------------------------------------------------------------
# Q5 哨兵决策机（题面 Q5·裁判系统决策规则表）
# ---------------------------------------------------------------------------


class SentryState(Enum):
    """哨兵状态机（已提供，勿改）。"""

    PATROL = "PATROL"
    SUSPECT = "SUSPECT"
    ENGAGE = "ENGAGE"
    RETREAT = "RETREAT"
    RETURN = "RETURN"




def decide(sensor, state, hp, heat):
    """Apply R1-R7 in order; heat does not override the specified rules."""

    fields = {"enemy_frames", "enemy_dist", "robot_type", "max_hp"}

   
    if not isinstance(state, SentryState):
        raise ValueError("State must be a SentryState member")

    
    if not isinstance(sensor, dict) or not fields.issubset(sensor):
        raise ValueError("Sensor is missing required fields")

    frames = sensor["enemy_frames"]
    if not isinstance(frames, (tuple, list)):
        frames = (False,)
    elif not 1 <= len(frames) <= 6:
        raise ValueError("Enemy history must contain one to six frames")

   
    frames = tuple(bool(frame) for frame in frames)
    visible = frames[-1]
    distance = _as_int(sensor["enemy_dist"], default=None)
    distance = float("inf") if distance is None else max(0, distance)
    robot_type = sensor["robot_type"]

    if isinstance(robot_type, str):
        robot_type = robot_type.strip().upper()
    if robot_type != "HERO":
        robot_type = "INFANTRY"
    hp_pct = hp_ratio(hp, sensor["max_hp"])

    if hp_pct <= 30:  # R1: survival takes precedence over every state.
        return "RETREAT", SentryState.RETREAT

    if state is SentryState.RETREAT:  # R2: use recovery hysteresis.
        if hp_pct >= 60:
            return "RETURN", SentryState.RETURN
        return "RETREAT", SentryState.RETREAT

    if state is SentryState.RETURN:  # R3: return lasts one frame.
        return "MOVE_BASE", SentryState.PATROL

    if state is SentryState.ENGAGE:
        if visible:  # R4
            return _engagement_action(distance, robot_type)
        if len(frames) >= 3 and not any(frames[-3:]):  # R5
            return "SCAN", SentryState.SUSPECT
        return "HOLD_FIRE", SentryState.ENGAGE

    if visible:  # R6: require consecutive confirmation frames.
        if len(frames) >= 2 and frames[-2]:
            return _engagement_action(distance, robot_type)
        return "SCAN", SentryState.SUSPECT

    if state is SentryState.PATROL:  # R7
        return "PATROL_MOVE", SentryState.PATROL
    return "SCAN", SentryState.SUSPECT


def _engagement_action(distance, robot_type):
    """Share the identical engagement behavior required by R4 and R6."""
    if distance <= 3:
        return "SHOOT", SentryState.ENGAGE
    action = "MOVE_RIGHT" if robot_type == "HERO" else "MOVE_LEFT"
    return action, SentryState.ENGAGE


# ---------------------------------------------------------------------------
# Q6 巡逻任务（题面 Q6·巡逻契约与验收阈值）
# ---------------------------------------------------------------------------



def run_patrol(grid, max_steps=500):
    """Follow greedy steps and use a BFS detour to escape local minima.

    Resume greedy navigation once closer than the stalled position. Steps
    count forward attempts; visited cells include the initial position.
    """
    
    steps = 0
    visited = {grid.current_pos}
    detour = deque()
    entry_distance = 0

    
    while (steps < max_steps and grid.fuel > 0 and not grid.found_enemy):

        position = grid.current_pos
        distance = _manhattan(position, grid.enemy_pos)
        direction = next_step_toward(
            position, grid.enemy_pos, grid.obstacles, grid.facing)

        if detour and distance < entry_distance:
            detour.clear()

        if not detour:
            dx, dy = direction.delta
            neighbor = (position[0] + dx, position[1] + dy)

            if (grid.is_blocked(*neighbor) or _manhattan(neighbor, grid.enemy_pos) >= distance):
                obstacles = set(grid.obstacles)
                obstacles.update(_border_ring(grid.width, grid.height))
                path = _bfs_path(position, grid.enemy_pos, obstacles)

                if path is None:
                    break
                detour.extend(path)
                entry_distance = distance

        if detour:
            direction = detour.popleft()
        _face_direction(grid, direction)
        grid.move_forward()
        steps += 1
        visited.add(grid.current_pos)

    return {
        "steps": steps,
        "collisions": grid.collision_count,
        "visited_count": len(visited),
        "found_enemy": grid.found_enemy,
        "success": grid.found_enemy,
    }


def _manhattan(start, target):
    """Return distance on an obstacle-free four-neighbor grid."""
    return abs(start[0] - target[0]) + abs(start[1] - target[1])


def _border_ring(width, height):
    """Enclose a finite grid for searches that only inspect obstacles."""
    ring = {(x, -1) for x in range(-1, width + 1)}
    ring.update((x, height) for x in range(-1, width + 1))
    ring.update((-1, y) for y in range(-1, height + 1))
    ring.update((width, y) for y in range(-1, height + 1))
    return ring


def _face_direction(grid, direction):
    """Align the vehicle using at most two quarter turns."""
    clockwise = (Facing.UP, Facing.RIGHT, Facing.DOWN, Facing.LEFT)
    turns = (clockwise.index(direction) - clockwise.index(grid.facing)) % 4
    if turns == 3:
        grid.turn_left()
    else:
        for _ in range(turns):
            grid.turn_right()


def report_to_json(stats):
    """Serialize with sorted keys and stable, compact separators."""
    return json.dumps(stats, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


# ---------------------------------------------------------------------------
# Bonus：BFS 全局最短路（题面 Bonus·BFS 语义与排行榜）
# ---------------------------------------------------------------------------
def bfs_path_length(start, target, obstacles):
    """Return the shortest distance, or -1 if the target is unreachable.

    The caller must enclose the search space with boundary obstacles.
    Identical endpoints have distance zero, even if that cell is blocked.
    """
    path = _bfs_path(start, target, set(obstacles))
    return -1 if path is None else len(path)


def _bfs_path(start, target, obstacles):
    """Find a shortest sequence of headings using a FIFO frontier."""
    if start == target:
        return []
    if start in obstacles or target in obstacles:
        return None
    frontier = deque([start])
    parents = {start: None}
    while frontier:
        position = frontier.popleft()
        for direction in Facing:
            dx, dy = direction.delta
            neighbor = (position[0] + dx, position[1] + dy)
            if neighbor in obstacles or neighbor in parents:
                continue
            parents[neighbor] = (position, direction)
            if neighbor == target:
                path = []
                while neighbor != start:
                    neighbor, heading = parents[neighbor]
                    path.append(heading)
                path.reverse()
                return path
            frontier.append(neighbor)
    return None


# ---------------------------------------------------------------------------
# 渲染（已提供，demo 专用，不进测试）
# ---------------------------------------------------------------------------
def render_frame(grid, trail=()):
    """ASCII 渲染一帧战场；trail 为走过的格子集合。返回 list[str]。"""
    trail = set(trail)
    rows = []
    for y in range(grid.height - 1, -1, -1):
        row = []
        for x in range(grid.width):
            if (x, y) == grid.current_pos:
                row.append("◉")
            elif (x, y) == grid.enemy_pos:
                row.append("▲")
            elif (x, y) in grid.obstacles:
                row.append("█")
            elif (x, y) in trail:
                row.append("·")
            else:
                row.append(".")
        rows.append("".join(row))
    return rows

#版本溯源免责声明，仅供学习与参考！！！！！！！！！！！！！！！！！！！！！！！！
# === BEGIN SOURCE PROVENANCE v1 ===
# This block is deliberately separate from the implementation fingerprint.
# Verification is opt-in: importing and using the module behaves as before.
SOURCE_PROVENANCE = {
    "source_id": "SENTRY-REF-20261008-E55343F2C79D",
    "created_on": "2026-10-08",
    "algorithm": "sha256-python-ast-v1",
    "implementation_sha256": 'a314fee858852e60ec4b0a18526d4ba4e5e0abf8b71f818b984c6b9c77c7e09c',
    "signed": False,
}


def verify_source_provenance(path=None):
    """Compare source code with this reference's recorded implementation.

    With no path, inspect this module's source file. Pass another path to
    compare a distributed copy with this reference. Formatting, comments,
    and docstrings are ignored; identifier and implementation changes are
    detected. The provenance block itself is outside the fingerprint.

    This unsigned check does not prove authorship, permission, independent
    work, or meaningful modification. Both the marker and checker can be
    removed or altered by anyone who can edit the source file.
    """
    import ast
    import hashlib
    from pathlib import Path

    def canonical(node):
        if isinstance(node, list):
            return tuple(canonical(item) for item in node)
        if not isinstance(node, ast.AST):
            return node
        fields = []
        for name, value in ast.iter_fields(node):
            if name == "type_comment":
                continue
            if name == "type_params" and not value:
                continue
            if (name == "body" and value
                    and isinstance(node, (ast.Module, ast.ClassDef,
                                          ast.FunctionDef,
                                          ast.AsyncFunctionDef))):
                first = value[0]
                if (isinstance(first, ast.Expr)
                        and isinstance(first.value, ast.Constant)
                        and isinstance(first.value.value, str)):
                    value = value[1:]
            fields.append((name, canonical(value)))
        return type(node).__name__, tuple(fields)

    report = {
        "source_id": SOURCE_PROVENANCE["source_id"],
        "algorithm": SOURCE_PROVENANCE["algorithm"],
        "expected_sha256": SOURCE_PROVENANCE["implementation_sha256"],
        "actual_sha256": None,
        "matches_reference": None,
        "status": "unavailable",
        "signed": False,
    }
    try:
        source_path = Path(path if path is not None else __file__)
        text = source_path.read_text(encoding="utf-8-sig")
        tree = ast.parse(text)
        implementation = []
        for node in tree.body:
            if (isinstance(node, ast.FunctionDef)
                    and node.name == "verify_source_provenance"):
                continue
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == "SOURCE_PROVENANCE"):
                continue
            implementation.append(node)
        tree.body = implementation
        fingerprint = hashlib.sha256(
            repr(canonical(tree)).encode("utf-8")).hexdigest()
    except (OSError, UnicodeError, SyntaxError, TypeError, ValueError,
            NameError, RecursionError) as exc:
        report["error"] = str(exc)
        return report
    report["actual_sha256"] = fingerprint
    report["matches_reference"] = (
        fingerprint == report["expected_sha256"])
    report["status"] = (
        "unchanged" if report["matches_reference"] else "modified")
    return report
# === END SOURCE PROVENANCE v1 ===
