from PIL import Image, ImageOps
import os

def process_images(input_image_path, target_folder_path, frametime):
    # 获取原图片
    original_image = Image.open(input_image_path)
    orig_width, orig_height = original_image.size

    # 计算切片数量
    slice_count = orig_width // 16

    # 创建输出文件夹
    output_folder_path = os.path.join(target_folder_path, 'output')
    if not os.path.exists(output_folder_path):
        os.makedirs(output_folder_path)

    # 遍历目标文件夹下所有名字不带OVERLAY的png图片
    for filename in os.listdir(target_folder_path):
        if filename.endswith('.png') and 'OVERLAY' not in filename:
            image_path = os.path.join(target_folder_path, filename)
            target_image = Image.open(image_path)

            # 复制并竖直方向拼接目标图片
            new_image = Image.new('RGBA', (orig_width, orig_height))
            for i in range(slice_count):
                new_image.paste(target_image, (0, i * target_image.height))

            # 调整拼接后的图片
            new_image = new_image.crop((0, 0, orig_width, orig_height))

            # 叠加原图片并使用正片叠底和剪贴蒙版
            mask = ImageOps.grayscale(original_image)
            blended_image = Image.composite(new_image, original_image, mask)

            # 保存生成的图片
            output_image_path = os.path.join(output_folder_path, filename)
            blended_image.save(output_image_path, 'PNG')

            # 生成 .mcmeta 文件
            mcmeta_content = f"""{{
  "animation": {{
    "frametime": 2
  }}
}}
"""
            mcmeta_filename = os.path.join(output_folder_path, f"{filename}.mcmeta")
            with open(mcmeta_filename, 'w') as mcmeta_file:
                mcmeta_file.write(mcmeta_content)

# 示例用法
input_image_path = 'E:\\Github\\Modernity-GTNH\\未完成部分\\gt新的materialicons部分\\capsule.png'
target_folder_path = 'E:\\Github\\Modernity-GTNH\\未完成部分\\gt新的materialicons部分\\hotprotohalkonite'
frametime = 1
process_images(input_image_path, target_folder_path, frametime)