"""
合并 Tom Agent 文件
"""
import os

# 定义文件路径
base_dir = r"d:\Mirofish\AIAdPlacer\backend\app"
output_file = os.path.join(base_dir, "tom_agent.py")
part1_file = os.path.join(base_dir, "tom_agent_part1.py")
part2_file = os.path.join(base_dir, "tom_agent_part2.py")

# 合并文件
print(f"开始合并 Tom Agent 文件...")
with open(output_file, 'w', encoding='utf-8') as fout:
    for part_file in [part1_file, part2_file]:
        print(f"正在合并: {os.path.basename(part_file)}")
        with open(part_file, 'r', encoding='utf-8') as fin:
            fout.write(fin.read())
        fout.write("\n")  # 添加换行符分隔

print(f"文件合并完成: {output_file}")

# 删除临时文件
print("清理临时文件...")
for part_file in [part1_file, part2_file]:
    if os.path.exists(part_file):
        os.remove(part_file)
        print(f"已删除: {os.path.basename(part_file)}")

print("完成！")
