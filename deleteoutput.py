import os
import shutil

def delete_all_output_folders(root_dir):
    """
    递归删除指定根目录下**所有层级**中名为 output 的文件夹及其全部内容
    :param root_dir: 要扫描的根目录路径
    """
    # 检查根目录是否存在
    if not os.path.isdir(root_dir):
        print(f"❌ 错误：目录不存在 → {root_dir}")
        return

    print(f"✅ 开始扫描目录：{root_dir}")
    print("=" * 60)

    deleted_count = 0  # 统计删除的 output 文件夹数量

    # 递归遍历所有目录（topdown=False 更安全，避免遍历已删除目录）
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        # 判断当前目录是否是 output
        if os.path.basename(dirpath) == "output":
            try:
                # 删除整个 output 文件夹（包括里面所有文件/子文件夹）
                shutil.rmtree(dirpath)
                print(f"🗑️ 已删除：{dirpath}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ 删除失败：{dirpath}，原因：{str(e)}")

    print("=" * 60)
    print(f"✅ 扫描完成！总共删除了 {deleted_count} 个 output 文件夹")

if __name__ == "__main__":
    print("===== 批量删除所有 output 子文件夹工具 =====")
    # 获取用户输入的目录
    target_dir = input("请输入要扫描的根目录路径：").strip()
    
    # 执行删除
    delete_all_output_folders(target_dir)
    input("\n按回车键退出...")