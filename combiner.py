import os
import sys
from tqdm import tqdm  # 导入 tqdm 用于显示进度条

def generate_tree(root_dir):
    """生成类似 tree /f 的目录树字符串"""
    tree_output = [root_dir]
    for root, dirs, files in os.walk(root_dir):
        level = root.replace(root_dir, '').count(os.sep)
        indent = '    ' * level
        if level > 0:  # 避免重复输出根目录
            tree_output.append(f"{indent}{os.path.basename(root)}")
        for file in files:
            tree_output.append(f"{indent}    {file}")
    return "\n".join(tree_output)

def concatenate_files(root_dir, output_file):
    # 计算总文件数以初始化进度条
    total_files = sum(len(files) for _, _, files in os.walk(root_dir))
    
    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 写入目录树
        outfile.write("Directory Tree:\n")
        outfile.write(generate_tree(root_dir) + "\n")
        outfile.write("=====\n\n")
        
        # 使用 tqdm 显示进度条
        with tqdm(total=total_files, desc="处理文件中", unit="file") as pbar:
            for root, dirs, files in os.walk(root_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            outfile.write("FILE: " + file_path + "\n")
                            outfile.write(content + "\n")
                            outfile.write("-----\n")
                        # 打印处理成功的文件信息
                        print(f"已处理: {file_path} - 成功")
                    except Exception as e:
                        outfile.write(f"FILE: {file_path}\n")
                        outfile.write(f"读取文件出错: {str(e)}\n")
                        outfile.write("-----\n")
                        # 打印处理失败的文件信息
                        print(f"已处理: {file_path} - 错误: {str(e)}")
                    # 更新进度条
                    pbar.update(1)

if __name__ == "__main__":
    # 如果有命令行参数，取第一个参数作为 root_dir，否则使用当前目录
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    output_file = 'project_text.txt'
    concatenate_files(root_dir, output_file)
    print(f"项目文件已合并到 {output_file}")
