import os
import shutil

# 指定你的目标图片和文件夹路径
target_image = 'E:/Github/Modernity-GTNH/assets/ic2/textures/items/itemCable.png'
folder_path = 'E:/Github/Modernity-GTNH/未完成部分/ic2/textures/items/新建文件夹'

# 获取文件夹中所有的文件名
file_list = os.listdir(folder_path)

# 遍历文件夹中的所有文件
for file_name in file_list:
    # 如果文件是png图片
    if file_name.endswith('.png'):
        # 构造源文件路径和目标文件路径
        file_path = os.path.join(folder_path, file_name)
        # 删除原有的png文件
        os.remove(file_path)
        # 复制目标图片到原有文件路径
        shutil.copy(target_image, file_path)

print("替换完成!")
