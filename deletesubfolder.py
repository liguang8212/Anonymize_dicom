import os
import shutil

def flatten_directory(root_path):
    if not os.path.isdir(root_path):
        print(f"❌ 目录不存在：{root_path}")
        return

    # 获取所有一级子目录
    first_level_dirs = [
        d for d in os.listdir(root_path)
        if os.path.isdir(os.path.join(root_path, d))
    ]

    print(f"✅ 找到 {len(first_level_dirs)} 个一级子目录")

    for first_dir in first_level_dirs:
        first_path = os.path.join(root_path, first_dir)
        print(f"\n━━━━━━ 处理目录：{first_path} ━━━━━━")

        # 1. 把所有子文件夹里的文件移动到一级目录
        for root, dirs, files in os.walk(first_path):
            if root == first_path:
                continue

            for file in files:
                src = os.path.join(root, file)
                dst = os.path.join(first_path, file)

                # 处理重名
                counter = 1
                while os.path.exists(dst):
                    name, ext = os.path.splitext(file)
                    dst = os.path.join(first_path, f"{name}_{counter}{ext}")
                    counter += 1

                shutil.move(src, dst)
                print(f"移动：{src} → {dst}")

        # 2. 删除所有空目录（彻底清理）
        for root, dirs, files in os.walk(first_path, topdown=False):
            if root == first_path:
                continue
            try:
                os.rmdir(root)
                print(f"已删除空目录：{root}")
            except OSError:
                pass

    print("\n🎉 全部处理完成：文件已上移，空目录已全部删除！")

if __name__ == "__main__":
    target = input("请输入根目录路径：").strip()
    flatten_directory(target)