import os
from PIL import Image
import glob
import shutil

def change_color(image_path):
    with Image.open(image_path) as img:
        img = img.convert("RGBA")
        datas = img.getdata()
        new_data = []
        for item in datas:
            if item[3] != 0:  # If not transparent
                new_data.append((63, 255, 0, item[3]))  # Change color to #3fff00
            else:
                new_data.append(item)
        img.putdata(new_data)
        img.save(image_path)

def rename_and_process_images(base_path):
    for root, dirs, files in os.walk(base_path):
        for file_name in files:
            if file_name.endswith(".png"):
                file_path = os.path.join(root, file_name)
                change_color(file_path)
                base, ext = os.path.splitext(file_path)
                new_name = base + "_s" + ext
                os.rename(file_path, new_name)

def delete_mcmeta_files(base_path):
    mcmeta_files = glob.glob(os.path.join(base_path, '**/*.mcmeta'), recursive=True)
    for mcmeta_file in mcmeta_files:
        os.remove(mcmeta_file)

def delete_non_block_and_items_folders(base_path):
    for root, dirs, files in os.walk(base_path):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            if dir_name == "items" or (dir_name != "block" and "block" in os.listdir(root)):
                shutil.rmtree(dir_path)

if __name__ == "__main__":
    base_path = "E:/Github/Modernity-GTNH/111"  # 将此路径替换为您要遍历的路径
    rename_and_process_images(base_path)
    delete_mcmeta_files(base_path)
    delete_non_block_and_items_folders(base_path)
