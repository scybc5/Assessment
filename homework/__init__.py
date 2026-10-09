# -*- coding: utf-8 -*-
#这是免责声明！
# Source reference: SENTRY-REF-20261008-E55343F2C79D
# The provenance block at the end provides an optional integrity check.
# This reference must not be presented as independently authored work.
# An unsigned fingerprint is a comparison aid, not proof of authorship.

# 导入需要的模块
import json
from collections import deque
from enum import Enum #关于Facing

# ---------------------------------------------------------------------------
# 仿真世界基础
# ---------------------------------------------------------------------------
class Facing(Enum):
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    def get_delta(self):
        # self.value 获取枚举绑定的元组
        dx = self.value[0]
        dy = self.value[1]
        return (dx, dy)
'''
1.class Facing(Enum): 创建枚举类,枚举用来存固定4个方向常量
2.def get_delta(self): 传入实例自身self
3.dx = self.value[0]:取出元组第0项x偏移;dy取出y偏移
4.return (dx,dy) 返回方向移动一步的坐标变化量
'''

# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
def _as_int(value, default=0):
    """安全转化整数,转换失败返回default默认值"""
    try:
        result = int(value)
        return result
    except (TypeError, ValueError, OverflowError):
        # 出现这三类异常，代表转换失败，返回默认值
        return default
'''
except捕获三类错误:
  TypeError:类型不能转
  ValueError:字符串文本不能转数字
  OverflowError:数字超大溢出
'''

def hp_ratio(hp, max_hp):
    """血量百分比，返回 0-100 的 int"""
    hp = _as_int(hp)
    max_hp = _as_int(max_hp)
    if max_hp <= 0:
        return 0
    # max(0, min(hp, max_hp))：血量限制 0~max_hp
    temp = min(hp, max_hp)
    temp = max(0, temp)
    percent = temp * 100 // max_hp
    return percent


def status_report(name, robot_type, hp, max_hp, battery):
    """生成机器人状态格式化报告字符串"""
    battery_raw = _as_int(battery)
    # 电量限制 0~100
    battery = min(100, battery_raw)
    battery = max(0, battery)

    if battery >= 60:
        level = "OK"
    elif battery >= 20:
        level = "WARNING"
    else:
        level = "LOW"

    hp_percent = hp_ratio(hp, max_hp)
    # 注意格式
    output = "{:<10}|{:^10}|HP {:>3}%|BAT {:>3}%|{}".format(
        name, robot_type, hp_percent, battery, level
    )
    return output


# ---------------------------------------------------------------------------
# Q2 战斗日志分析（题面 Q2·多源日志解析与统计）
# ---------------------------------------------------------------------------
def analyze_damage_log(lines):
    """解析日志列表，统计护甲伤害，返回统计字典"""
    SEEN_ids = set()
    EVENT_count = 0
    # 替换defaultdict，普通字典手动初始化护甲，初始伤害0
    by_armor = {}
    by_armor["front"] = 0
    by_armor["left"] = 0
    by_armor["right"] = 0

    # 将输入lines转为迭代器；捕获不可迭代对象异常
    try:
        source = iter(lines)
    except TypeError:
        source = iter([])

    for line in source:
        # 如果不是字符串，跳过这一行
        if not isinstance(line, str):
            continue
        line = line.strip()
        # 空行或者#注释开头，跳过
        if len(line) == 0 or line.startswith("#"):
            continue

        events = []
        try:
            if line.startswith("{"):
                # JSON格式日志行
                RECORD = json.loads(line)
                armor = RECORD["armor"]
                damage = RECORD["damage"]
                # 伤害不是整数跳过
                if type(damage) is not int:
                    continue
                if damage <= 0:
                    continue
                # 判断是否存在id字段，做去重
                if "id" in RECORD:
                    Event_id = RECORD["id"]
                    if Event_id in SEEN_ids:
                        continue
                    SEEN_ids.add(Event_id)
                events.append((armor, damage))
            else:
                # 传感器文本格式日志，调用解析函数
                events = _parse_sensor_damage(line)
        except (TypeError, ValueError, KeyError, RecursionError):
            # 当前行解析出错，直接跳过
            continue

        for armor, damage in events:
            # 如果护甲不在字典，新增，初始值0
            if armor not in by_armor:
                by_armor[armor] = 0
            by_armor[armor] = by_armor[armor] + damage
            EVENT_count = EVENT_count + 1

    # 计算全部伤害总和
    total = 0
    for val in by_armor.values():
        total = total + val

    average = 0.0
    try:
        if EVENT_count > 0:
            average = total / EVENT_count
            average = round(average, 2)
        else:
            average = 0.0
    except OverflowError:
        average = float("inf")

    # 找受到伤害最高的护甲
    most_hit = None
    if EVENT_count > 0:
        max_dmg = -1
        for key in by_armor:
            dmg_val = by_armor[key]
            if dmg_val > max_dmg:
                max_dmg = dmg_val
                most_hit = key

    result_dict = {
        "total": total,
        "by_armor": by_armor,
        "most_hit": most_hit,
        "avg": average
    }
    return result_dict
'''
1.SEEN_ids = set() 集合,存放已经处理的事件id,实现日志去重
2.EVENT_count =0 统计有效伤害事件总数量
3.try source=iter(lines)：把输入转迭代器；如果输入不能迭代，设置空迭代器
4.内层try-except捕获单行解析错误;单行出错不终止整个日志解析
5.if line.startswith("{"):判断是否JSON日志
    json.loads(line)把json文本转为python字典RECORD
    取出armor护甲标识、damage伤害;伤害非int、<=0直接跳过
    如果日志带有id,判断是否已经处理过,实现去重
    将(armor,damage)加入events列表
6.else:传感器格式日志,调用_parse_sensor_damage(line)
7.except捕获解析异常,continue丢弃本行
8.for armor,damage in events循环每一条伤害事件
    if armor not in by_armor:护甲不存在就初始化为0
    by_armor[armor] += damage;EVENT_count自增
9.循环求和得到total总伤害
10.if EVENT_count>0 计算平均伤害round保留两位小数;溢出设无穷大inf
11.手动for循环遍历字典找伤害最大护甲\
12.组装result_dict字典返回,包含total,by_armor,most_hit,avg
'''

def _parse_sensor_damage(line):
    """解析逗号冒号分隔传感器日志，返回[(护甲全名,伤害),...]"""
    armor_names = {"F": "front", "L": "left", "R": "right"}
    events = []
    # 按逗号分割字符串
    segment_list = line.split(",")
    for segment in segment_list:
        # 按冒号切分
        part_list = segment.split(":")
        armor_raw = part_list[0].strip()
        value_raw = part_list[1].strip()

        if not value_raw.isascii() or not value_raw.isdecimal():
            raise ValueError("Damage must contain decimal digits")
        damage = int(value_raw)
        if damage <= 0:
            raise ValueError("Damage must be positive")
        full_armor_name = armor_names[armor_raw]
        events.append((full_armor_name, damage))
    return events
'''
1.segment_list = line.split(",") 把"F:10,L:20"切分成 ["F:10","L:20"]
4.for segment in segment_list遍历每一段
5.part_list = segment.split(":") 将"F:10"切分为 ["F","10"]
6.armor_raw = part_list[0].strip()去除左右空白;value_raw = part_list[1].strip()
7.value_raw.isascii() 判断是否ascii字符;isdecimal() 判断纯数字文本
    不满足抛出ValueError,外层analyze_damage_log捕获异常跳过该行
8.damage = int(value_raw)转为整数伤害
9.if damage <=0:伤害必须正数，否则抛异常
10.full_armor_name查表得到护甲完整名字
11.events.append((full_armor_name, damage))加入结果列表
12.return events返回解析后的事件列表
'''

# ---------------------------------------------------------------------------
# Q3 SentryGrid（题面 Q3·载体物理规则）
# ---------------------------------------------------------------------------
class SentryGrid:
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
        # 调用setter设置位置
        self.set_current_pos(start_pos)

    def _clamp_cell(self, cell):
        """已提供：元素转 int 并夹回地图范围（供 __init__ 使用）。"""
        x = int(cell[0])
        y = int(cell[1])
        x = max(0, min(self._width - 1, x))
        y = max(0, min(self._height - 1, y))
        return (x, y)

    def get_width(self):
        return self._width
    def get_height(self):
        return self._height
    def get_enemy_pos(self):
        return self._enemy_pos
    def get_facing(self):
        return self._facing
    def get_fuel(self):
        return self._fuel
    def get_collision_count(self):
        return self._collision_count
    def get_obstacles(self):
        return self._obstacles

    def get_found_enemy(self):
        pos = self.get_current_pos()
        enemy = self.get_enemy_pos()
        return pos == enemy

    def is_blocked(self, x, y):
        """已提供:坐标是否为障碍或越界(O(1))。"""
        in_obstacle = (x, y) in self._obstacles
        in_border = (0 <= x < self._width) and (0 <= y < self._height)
        return in_obstacle or (not in_border)

    def get_current_pos(self):
        """获取当前位置 (x, y) 的 tuple。"""
        return self._pos

    def set_current_pos(self, value):
        """设置坐标，转换、限制边界，拒绝障碍物格子"""
        if not isinstance(value, (tuple, list)) or len(value) != 2:
            raise TypeError("Position must be a tuple or list of length two")
        position = self._clamp_cell(value)
        if position in self._obstacles:
            raise ValueError("Position cannot be on an obstacle")
        self._pos = position

    def move_forward(self):
        if self._fuel <= 0:
            return self.get_current_pos()
        self._fuel = self._fuel - 1
        dx, dy = self._facing.get_delta()
        pos_now = self.get_current_pos()
        position = (pos_now[0] + dx, pos_now[1] + dy)

        if self.is_blocked(position[0], position[1]):
            self._collision_count = self._collision_count + 1
        else:
            self.set_current_pos(position)
        return self.get_current_pos()

    def turn_left(self):
        dx, dy = self._facing.get_delta()
        new_tuple = (-dy, dx)
        self._facing = Facing(new_tuple)
        return self._facing

    def turn_right(self):
        dx, dy = self._facing.get_delta()
        new_tuple = (dy, -dx)
        self._facing = Facing(new_tuple)
        return self._facing
'''
1.__init__构造函数:初始化地图宽高、障碍物集合、敌人坐标、朝向、燃料、碰撞计数;调用set_current_pos设置初始位置
2._clamp_cell:把坐标强制限制在地图合法范围内
3.get_found_enemy():判断当前位置是否等于敌人位置
4.is_blocked(x,y) 判断坐标越界或者属于障碍物
5.get_current_pos()读取位置;set_current_pos(value)设置位置，做类型校验、边界限制、障碍物校验
6.move_forward():向前移动;燃料-1;计算下一步坐标；被阻挡则碰撞计数+1,否则更新位置;返回当前坐标
7.turn_left左转:根据位移向量计算新方向元组构造Facing枚举;右转同理
'''

# ---------------------------------------------------------------------------
# Q4 贪心导航（题面 Q4·单步贪心导航策略）
# ---------------------------------------------------------------------------
def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
    dx_total = target[0] - pos[0]
    dy_total = target[1] - pos[1]

    if dx_total > 0:
        horizontal = Facing.RIGHT
    else:
        horizontal = Facing.LEFT

    if dy_total > 0:
        vertical = Facing.UP
    else:
        vertical = Facing.DOWN

    candidates = []
    candidates.append((dx_total, horizontal))
    candidates.append((dy_total, vertical))

    if abs(dy_total) > abs(dx_total):
        # 交换列表两个元素
        temp = candidates[0]
        candidates[0] = candidates[1]
        candidates[1] = temp

    for difference, direction in candidates:
        if difference == 0:
            continue
        step_x, step_y = direction.get_delta()
        next_x = pos[0] + step_x
        next_y = pos[1] + step_y
        if (next_x, next_y) not in obstacles:
            return direction
    return current_facing
'''
1.dx_total = target[0] - pos[0]:x方向目标和当前位置差值
2.dy_total = target[1] - pos[1]:y方向差值
3.if-else判断:dx>0向右,否则向左;dy>0向上否则向下
4.candidates候选方向列表,存入(差值，方向)
5.if abs(dy_total)>abs(dx_total):y方向差距更大,交换列表顺序,优先尝试y方向
6.for循环遍历候选方向
    difference==0跳过该方向;调用get_delta拿到移动偏移
    next_x next_y算出下一步坐标;如果该坐标不在障碍物集合,直接返回该方向
7.全部方向走不通,返回传入的current_facing保持原有朝向
'''

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
    fields = {"enemy_frames", "enemy_dist", "robot_type", "max_hp"}

    if not isinstance(state, SentryState):
        raise ValueError("State must be a SentryState member")

    if not isinstance(sensor, dict):
        raise ValueError("Sensor is missing required fields")
    all_ok = True
    for f in fields:
        if f not in sensor:
            all_ok = False
    if not all_ok:
        raise ValueError("Sensor is missing required fields")

    frames = sensor["enemy_frames"]
    if not isinstance(frames, (tuple, list)):
        frames = (False,)
    else:
        if not (1 <= len(frames) <= 6):
            raise ValueError("Enemy history must contain one to six frames")

    temp_list = []
    for item in frames:
        temp_list.append(bool(item))
    frames = tuple(temp_list)

    visible = frames[-1]
    distance = _as_int(sensor["enemy_dist"], default=None)
    if distance is None:
        distance = float("inf")
    else:
        if distance < 0:
            distance = 0

    robot_type = sensor["robot_type"]
    if isinstance(robot_type, str):
        robot_type = robot_type.strip().upper()
    if robot_type != "HERO":
        robot_type = "INFANTRY"

    hp_pct = hp_ratio(hp, sensor["max_hp"])

    # R1
    if hp_pct <= 30:
        return "RETREAT", SentryState.RETREAT
    # R2
    if state is SentryState.RETREAT:
        if hp_pct >= 60:
            return "RETURN", SentryState.RETURN
        else:
            return "RETREAT", SentryState.RETREAT
    # R3
    if state is SentryState.RETURN:
        return "MOVE_BASE", SentryState.PATROL
    # R4 R5
    if state is SentryState.ENGAGE:
        if visible:
            return _engagement_action(distance, robot_type)
        if len(frames) >= 3:
            slice_ok = True
            for idx in [-1, -2, -3]:
                if frames[idx]:
                    slice_ok = False
            if slice_ok:
                return "SCAN", SentryState.SUSPECT
        return "HOLD_FIRE", SentryState.ENGAGE
    # R6
    if visible:
        if len(frames)>=2 and frames[-2]:
            return _engagement_action(distance, robot_type)
        return "SCAN", SentryState.SUSPECT
    # R7
    if state is SentryState.PATROL:
        return "PATROL_MOVE", SentryState.PATROL

    return "SCAN", SentryState.SUSPECT

def _engagement_action(distance, robot_type):
    """Share the identical engagement behavior required by R4 and R6."""
    if distance <= 3:
        return "SHOOT", SentryState.ENGAGE
    if robot_type == "HERO":
        action = "MOVE_RIGHT"
    else:
        action = "MOVE_LEFT"
    return action, SentryState.ENGAGE
'''
1.fields集合存放sensor字典必须具备的key
2.frames敌人帧历史;校验长度1-6;循环全部元素转bool,组装tuple
3.visible取最后一帧是否看见敌人;distance调用_as_int;距离为空赋值无穷大inf,负数修正为0
4.robot_type:字符串去空格转大写;非HERO强制赋值INFANTRY
5.hp_pct获取血量百分比
6.按顺序执行R1-R7规则:
R1血量<=30%直接返回RETREAT撤退
R2处于RETREAT状态,血量>=60切RETURN,否则保持RETREAT
R3处于RETURN状态返回MOVE_BASE,切换PATROL巡逻
R4-R5 ENGAGE接战状态:看得见敌人调用_engagement_action;最近3帧全看不见 → SUSPECT怀疑;否则HOLD_FIRE
R6 当前帧可见敌人，上一帧也可见 →接战;否则SCAN怀疑
R7 PATROL巡逻状态返回PATROL_MOVE
全部条件不命中返回SCAN SUSPECT
7._engagement_action:距离≤3 返回SHOOT射击;HERO向右移动,INFANTRY向左移动,保持ENGAGE状态
'''

# ---------------------------------------------------------------------------
# Q6 巡逻任务（题面 Q6·巡逻契约与验收阈值）
# ---------------------------------------------------------------------------
def run_patrol(grid, max_steps=500):
    steps = 0
    visited = set()
    pos_start = grid.get_current_pos()
    visited.add(pos_start)
    detour = deque()
    entry_distance = 0

    cond1 = steps < max_steps
    cond2 = grid.get_fuel() > 0
    cond3 = not grid.get_found_enemy()
    while cond1 and cond2 and cond3:
        position = grid.get_current_pos()
        distance = _manhattan(position, grid.get_enemy_pos())
        direction = next_step_toward(
            position, grid.get_enemy_pos(), grid.get_obstacles(), grid.get_facing())

        if len(detour) > 0 and distance < entry_distance:
            detour.clear()

        if len(detour) == 0:
            dx, dy = direction.get_delta()
            neighbor_x = position[0] + dx
            neighbor_y = position[1] + dy
            neighbor = (neighbor_x, neighbor_y)
            dist_neighbor = _manhattan(neighbor, grid.get_enemy_pos())
            blocked = grid.is_blocked(neighbor_x, neighbor_y)
            if blocked or dist_neighbor >= distance:
                obstacles = set(grid.get_obstacles())
                border_set = _border_ring(grid.get_width(), grid.get_height())
                for b in border_set:
                    obstacles.add(b)
                path = _bfs_path(position, grid.get_enemy_pos(), obstacles)
                if path is None:
                    break
                for d in path:
                    detour.append(d)
                entry_distance = distance

        if len(detour) > 0:
            direction = detour.popleft()
        _face_direction(grid, direction)
        grid.move_forward()
        steps = steps + 1
        visited.add(grid.get_current_pos())

        cond1 = steps < max_steps
        cond2 = grid.get_fuel() > 0
        cond3 = not grid.get_found_enemy()

    visited_count = len(visited)
    stats = {
        "steps": steps,
        "collisions": grid.get_collision_count(),
        "visited_count": visited_count,
        "found_enemy": grid.get_found_enemy(),
        "success": grid.get_found_enemy(),
    }
    return stats

def _manhattan(start, target):
    x_diff = abs(start[0] - target[0])
    y_diff = abs(start[1] - target[1])
    return x_diff + y_diff

def _border_ring(width, height):
    ring = set()
    for x in range(-1, width + 1):
        ring.add((x, -1))
    for x in range(-1, width + 1):
        ring.add((x, height))
    for y in range(-1, height + 1):
        ring.add((-1, y))
    for y in range(-1, height + 1):
        ring.add((width, y))
    return ring

def _face_direction(grid, direction):
    clockwise = (Facing.UP, Facing.RIGHT, Facing.DOWN, Facing.LEFT)
    idx_now = 0
    for i in range(len(clockwise)):
        if clockwise[i] == grid.get_facing():
            idx_now = i
    idx_tar = 0
    for i in range(len(clockwise)):
        if clockwise[i] == direction:
            idx_tar = i
    turns = (idx_tar - idx_now) % 4
    if turns == 3:
        grid.turn_left()
    else:
        for _ in range(turns):
            grid.turn_right()

def report_to_json(stats):
    return json.dumps(stats, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))
'''
run_patrol:巡逻主循环;steps步数;visited记录走过格子;detour双端队列存储绕路BFS路径;
while循环条件:步数没超、燃料>0、没有找到敌人;
执行贪心导航,如果贪心下一步被阻挡或者距离没有缩短,调用_bfs_path获取绕路路径存入detour;
detour不为空就按BFS路径转向移动;每走一步steps+1记录访问格子
_manhattan:曼哈顿距离,x差绝对值+y差绝对值。
_border_ring:生成地图外围一圈虚拟障碍物集合。
_face_direction:遍历查找索引替代list.index();计算需要转动次数,turns==3等价左转一次,其余循环turns次右转,把机器人朝向转到目标方向。
report_to_json:调用json.dumps输出紧凑json字符串。
'''

# ---------------------------------------------------------------------------
# Bonus：BFS 全局最短路（题面 Bonus·BFS 语义与排行榜）
# ---------------------------------------------------------------------------
def bfs_path_length(start, target, obstacles):
    obs_copy = set(obstacles)
    path = _bfs_path(start, target, obs_copy)
    if path is None:
        return -1
    else:
        return len(path)

def _bfs_path(start, target, obstacles):
    if start[0]==target[0] and start[1]==target[1]:
        return []
    if start in obstacles or target in obstacles:
        return None
    frontier = deque()
    frontier.append(start)
    parents = dict()
    parents[start] = None
    while len(frontier) > 0:
        position = frontier.popleft()
        for direction in Facing:
            dx, dy = direction.get_delta()
            neighbor_x = position[0] + dx
            neighbor_y = position[1] + dy
            neighbor = (neighbor_x, neighbor_y)
            if neighbor in obstacles:
                continue
            if neighbor in parents:
                continue
            parents[neighbor] = (position, direction)
            if neighbor[0]==target[0] and neighbor[1]==target[1]:
                path = []
                cur = neighbor
                while not (cur[0]==start[0] and cur[1]==start[1]):
                    prev_pos, head = parents[cur]
                    path.append(head)
                    cur = prev_pos
                path.reverse()
                return path
            frontier.append(neighbor)
    return None
'''
bfs_path_length:调用_bfs_path;路径None返回-1;否则返回路径方向列表长度。
_bfs_path广度优先搜索找方向序列:
1.start等于target直接返回空列表;起点终点在障碍物返回None
2.frontier队列存放待访问格子;parents字典记录每个格子的(前驱位置，过来的方向)
3.while队列不为空:popleft取出队首position
4.遍历全部4个方向;计算neighbor相邻格子;障碍/已经访问过跳过
5.记录parents;到达target就回溯parents,收集方向path,reverse反转顺序返回路径;
6.全部遍历完没找到,返回None代表不可达。
'''

# ---------------------------------------------------------------------------
# 渲染（已提供，demo 专用，不进测试）
# ---------------------------------------------------------------------------
def render_frame(grid, trail=()):
    """ASCII 渲染一帧战场；trail 为走过的格子集合。返回 list[str]。"""
    trail = set(trail)
    rows = []
    h = grid.get_height()
    for y in range(h - 1, -1, -1):
        row = []
        w = grid.get_width()
        for x in range(w):
            pos_cur = grid.get_current_pos()
            enemy_pos = grid.get_enemy_pos()
            if x == pos_cur[0] and y == pos_cur[1]:
                row.append("◉")
            elif x == enemy_pos[0] and y == enemy_pos[1]:
                row.append("▲")
            elif (x, y) in grid.get_obstacles():
                row.append("█")
            elif (x, y) in trail:
                row.append("·")
            else:
                row.append(".")
        row_str = "".join(row)
        rows.append(row_str)
    return rows

#版本溯源免责声明，仅供学习与参考！！！！！！！！！！！！！！！！！！！！！！！！
# === BEGIN SOURCE PROVENANCE v1 ===
# This block is deliberately separate from the implementation fingerprint.
# Verification is opt‑in: importing and using the module behaves as before.
SOURCE_PROVENANCE = {
    "source_id": "SENTRY-REF-20261008-E55343F2C79D",
    "created_on": "2026-10-08",
    "algorithm": "sha256-python-ast-v1",
    "implementation_sha256": 'a314fee858852e60ec4b0a18526d4ba4e5e0abf8b71f818b984c6b9c77c7e09c',
    "signed": False,
}
def verify_source_provenance(path=None):
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
        text = source_path.read_text(encoding="utf‑8‑sig")
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
            repr(canonical(tree)).encode("utf‑8")).hexdigest()
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