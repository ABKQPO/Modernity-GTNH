import os

from PIL import Image

class ImageReader:
    def __init__(self, image_path):
        self.image_path = image_path
        self.images: [str] = []
        self._find_images()

    # 遍历路径下所有png图像 并记录
    def _find_images(self):
        """遍历指定路径下的所有 PNG 图像并记录到 images 列表中。"""
        if not os.path.exists(self.image_path):
            print(f"路径 '{self.image_path}' 不存在。")
            return

        # 遍历文件夹及其子文件夹中的所有文件
        for root, _, files in os.walk(self.image_path):
            for file in files:
                if file.lower().endswith('.png'):  # 检查文件扩展名是否为 .png
                    if self._checkIs16Width(os.path.join(root, file)):
                        pass
                    else:
                        print(f"{file} 宽度不为16")
                    full_path = os.path.join(root, file)
                    self.images.append(full_path)

    def _checkIs16Width(self, image_path):
        """检查图像是否为16宽度"""
        try:
            img = Image.open(image_path)
            width, height = img.size
            if width % 16 == 0:
                return True
            else:
                return False
        except Exception as e:
            print(f"无法打开图像 '{image_path}': {e}")
            return False



if __name__ == "__main__":
    image_path = input("请输入绝对路径：")
    reader = ImageReader(image_path)