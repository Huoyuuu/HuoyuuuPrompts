import os
import sys
from tqdm import tqdm  # 导入 tqdm 用于显示进度条

# --- 在这里手动配置需要包含或排除的文件后缀 ---
# 如果 INCLUDE_EXTENSIONS 非空，则只处理这些后缀的文件。
# 示例：['.py', '.txt', '.md'] 只处理 Python, 文本 和 Markdown 文件
# 留空 [] 表示默认包含所有文件 (除非被 EXCLUDE_EXTENSIONS 排除)。
INCLUDE_EXTENSIONS = []

# 如果 EXCLUDE_EXTENSIONS 非空，则跳过这些后缀的文件。
# 示例：['.log', '.tmp', '.bak', '.pyc'] 排除日志、临时、备份和Python编译文件
# 这个列表优先级高于 INCLUDE_EXTENSIONS，即如果一个后缀同时在两个列表中，它会被排除。
EXCLUDE_EXTENSIONS = ['.log', '.tmp', '.bak', '.pyc', '.swp', '.DS_Store',
                      '.csv', '.ttl', '.webp', '.jpg', '.png', '.lock', 'html', 'ts', 'svelte','css']

# --- 配置结束 ---

# 确保后缀都是小写且以 '.' 开头
include_exts = {ext.lower() if ext.startswith('.') else '.' +
                ext.lower() for ext in INCLUDE_EXTENSIONS}
exclude_exts = {ext.lower() if ext.startswith('.') else '.' +
                ext.lower() for ext in EXCLUDE_EXTENSIONS}
# 添加常见的不需要遍历的目录
EXCLUDE_DIRS = {'.git', '__pycache__', 'node_modules', '.vscode', '.idea', 'docs', 'examples'}


def should_process_file(file_path):
    """根据全局配置判断是否应处理文件"""
    # 获取文件扩展名（小写）
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    # 1. 检查是否在排除列表中
    if exclude_exts and ext in exclude_exts:
        return False

    # 2. 如果指定了包含列表，检查是否在包含列表中
    if include_exts and ext not in include_exts:
        return False

    # 3. 如果通过了以上检查，则处理该文件
    return True


def generate_tree(root_dir):
    """生成过滤后的目录树字符串，类似 tree /f"""
    tree_output = [os.path.abspath(root_dir)]
    items_to_add = []  # 用于收集所有符合条件的条目

    for root, dirs, files in os.walk(root_dir, topdown=True):
        # 过滤排除的目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        level = root.replace(os.path.abspath(root_dir), '').count(os.sep)
        indent = '│   ' * level
        sub_indent = indent + '├── '  # 默认连接符

        # 添加目录（仅当它不在根目录时）
        if root != os.path.abspath(root_dir):
            # 检查是否是最后一个目录（为了用└──），这比较复杂，简化处理
            items_to_add.append(
                f"{indent}└── {os.path.basename(root)}")  # 简化，都用└──表示目录

        # 过滤并添加文件
        filtered_files = sorted(
            [f for f in files if should_process_file(os.path.join(root, f))])

        for i, file in enumerate(filtered_files):
            if i == len(filtered_files) - 1:  # 最后一个文件用└──
                connector = '└── '
            else:
                connector = '├── '
            items_to_add.append(f"{indent}│   {connector}{file}")  # 文件前的缩进和连接符

    tree_output.extend(items_to_add)
    return "\n".join(tree_output)


def concatenate_files(root_dir, output_file):
    # 预先计算需要处理的文件总数和列表
    files_to_process = []
    for root, dirs, files in os.walk(root_dir, topdown=True):
        # 过滤排除的目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            file_path = os.path.join(root, file)
            if should_process_file(file_path):
                files_to_process.append(file_path)

    total_files = len(files_to_process)

    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 写入目录信息和过滤规则
        outfile.write(f"Project Root: {os.path.abspath(root_dir)}\n")
        filter_desc = []
        if include_exts:
            filter_desc.append(
                f"Included extensions: {', '.join(sorted(list(include_exts)))}")
        if exclude_exts:
            filter_desc.append(
                f"Excluded extensions: {', '.join(sorted(list(exclude_exts)))}")
        if not filter_desc:
            filter_desc.append("Processing all files.")
        outfile.write(f"Filters: {'; '.join(filter_desc)}\n")
        outfile.write("Excluded Dirs: " +
                      ', '.join(sorted(list(EXCLUDE_DIRS))) + "\n")
        outfile.write("=====\n\n")

        # 写入过滤后的目录树
        outfile.write("Directory Tree (filtered):\n")
        outfile.write(generate_tree(root_dir) + "\n")
        outfile.write("=====\n\n")

        # 写入文件内容
        outfile.write("File Contents:\n")
        outfile.write("=====\n\n")

        if total_files == 0:
            outfile.write("No files found matching the criteria.\n")
            print("根据过滤条件，没有找到需要处理的文件。")
            return  # 结束函数

        # 使用 tqdm 显示进度条
        with tqdm(total=total_files, desc="合并文件中", unit="file") as pbar:
            for file_path in files_to_process:  # 直接迭代筛选后的列表
                relative_path = os.path.relpath(file_path, root_dir)  # 使用相对路径
                try:
                    # 使用 'ignore' 忽略解码错误，避免中断
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                        outfile.write(f"--- START FILE: {relative_path} ---\n")
                        outfile.write(content + "\n")
                        outfile.write(f"--- END FILE: {relative_path} ---\n\n")
                    # 可以在控制台打印成功信息（可选）
                    # print(f"已处理: {relative_path} - 成功")
                except Exception as e:
                    outfile.write(f"--- START FILE: {relative_path} ---\n")
                    outfile.write(f"*** 读取文件时出错: {str(e)} ***\n")
                    outfile.write(f"--- END FILE: {relative_path} ---\n\n")
                    # 在控制台打印错误信息
                    print(f"\n处理文件时出错: {relative_path} - 错误: {str(e)}")
                # 更新进度条
                pbar.update(1)


if __name__ == "__main__":
    # 如果有命令行参数，取第一个参数作为 root_dir，否则使用当前目录
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    # 可以硬编码输出文件名，或者也从命令行获取第二个参数（如果提供）
    output_file = 'project_text.txt'
    if len(sys.argv) > 2:
        output_file = sys.argv[2]  # 允许指定输出文件名作为第二个参数

    # 打印将要执行的操作信息
    print(f"项目根目录: {os.path.abspath(root_dir)}")
    print(f"输出文件: {output_file}")
    filter_info = []
    if include_exts:
        filter_info.append(f"仅包含: {', '.join(sorted(list(include_exts)))}")
    if exclude_exts:
        filter_info.append(f"排除: {', '.join(sorted(list(exclude_exts)))}")
    if not filter_info:
        filter_info.append("处理所有文件")
    print(f"文件过滤规则: {'; '.join(filter_info)}")
    print(f"排除的目录: {', '.join(sorted(list(EXCLUDE_DIRS)))}")

    concatenate_files(root_dir, output_file)
    print(f"\n项目文件已根据指定规则合并到 {output_file}")
