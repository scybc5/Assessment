import json

from __init__ import analyze_damage_log

# 测试样例
if __name__ == "__main__":
    test_lines = [
        '{"armor":"front","damage":30,"id":7}',
        '{"armor":"front","damage":50,"id":7}', #重复id，跳过
        "F:32,L:5,R:12",
        "# this is comment",
        "",
        '{"armor":"left","damage":20}'
    ]
    res = analyze_damage_log(test_lines)
    print(res)