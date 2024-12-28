import io
import os

from PIL import Image
from PIL.ImageFile import ImageFile


class ImageSegmenter:
    def __init__(self, image_path: str, segment_height: int = 16):
        """
        初始化 ImageSegmenter。

        :param image_path: 输入图像路径。
        :param segment_height: 分割的高度，默认为 16。
        """
        self.image_path = image_path
        self.segment_height = segment_height
        self.images: list[io.BytesIO] = []  # 存储分割后的图像字节流
        self._segment_image()  # 初始化时分割图像

    def _segment_image(self):
        """将输入的图像分割为固定高度的图像块，并存储到 images 中。"""
        if not os.path.isfile(self.image_path):
            print(f"错误：路径 '{self.image_path}' 不存在或不是文件。")
            return

        try:
            # 打开图像文件
            with Image.open(self.image_path) as img:
                img = img.convert("RGBA")  # 确保图像为 RGBA 格式
                width, height = img.size  # 获取图像宽高
                for top in range(0, height, self.segment_height):
                    bottom = min(top + self.segment_height, height)  # 防止超出图像高度
                    # 裁剪图像区域 (左，上，右，下)
                    segment = img.crop((0, top, width, bottom))

                    # 保存图像到内存中的字节流
                    buffer = io.BytesIO()
                    segment.save(buffer, format='PNG')
                    buffer.seek(0)  # 重置流位置，方便后续读取
                    self.images.append(buffer)
        except IOError as e:
            print(f"图像打开失败: {e}")
        except Exception as e:
            print(f"图像处理失败: {e}")

    def get_segments_as_images(self) -> list[Image.Image]:
        """
        返回分割后的图像作为 Image.Image 对象列表。

        :return: Image.Image 对象列表。
        """
        segments = []
        for buffer in self.images:
            try:
                buffer.seek(0)  # 确保流从头部读取
                segments.append(Image.open(buffer))
            except Exception as e:
                print(f"加载图像块失败: {e}")
        return segments

    def get_as_image(self, index: int):
        """
        返回指定索引的分割图像。
        :param index: 分割图像的索引。
        :return: 分割图像。
        """
        bytes = self.images[index]
        try:
            bytes.seek(0)  # 确保流从头部读取
            return Image.open(bytes)
        except Exception as e:
            print(f"加载图像块失败: {e}")


if __name__ == "__main__":
    image_path = input("请输入绝对路径：")
    segmenter = ImageSegmenter(image_path)
    for i, image in enumerate(segmenter.images):
        print(f"Image {i+1}: {image.__sizeof__()}")
    image = segmenter.get_as_image(0)
    image.show()