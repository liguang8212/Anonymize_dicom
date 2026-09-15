import os
import shutil

def delete_keyword_folders(root_dir):
    """
    递归删除指定根目录下**所有层级**中名称包含 flow 或 dynamic 的文件夹及其全部内容
    :param root_dir: 要扫描的根目录路径
    """
    # 检查根目录是否存在
    if not os.path.isdir(root_dir):
        print(f"❌ 错误：目录不存在 → {root_dir}")
        return

    print(f"✅ 开始扫描目录：{root_dir}")
    print("=" * 60)

    deleted_count = 0  # 统计删除的目标文件夹数量
    # 定义需要匹配的关键字（不区分大小写，如需区分则去掉后续的.lower()）
    keywords = ["flow", "dynamic"]

    # 递归遍历所有目录（topdown=False 更安全，避免遍历已删除目录）
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=False):
        folder_name = os.path.basename(dirpath).lower()  # 统一转为小写，实现不区分大小写匹配
        # 判断当前文件夹名称是否包含任一关键字
        if any(keyword in folder_name for keyword in keywords):
            try:
                # 删除整个文件夹（包括里面所有文件/子文件夹）
                shutil.rmtree(dirpath)
                print(f"🗑️ 已删除：{dirpath}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ 删除失败：{dirpath}，原因：{str(e)}")

    print("=" * 60)
    print(f"✅ 扫描完成！总共删除了 {deleted_count} 个包含 flow/dynamic 的文件夹")

if __name__ == "__main__":
    print("===== 批量删除包含 flow/dynamic 的子文件夹工具 =====")
    # 获取用户输入的目录
    target_dir = input("请输入要扫描的根目录路径：").strip()
    
    # 执行删除
    delete_keyword_folders(target_dir)
    input("\n按回车键退出...")