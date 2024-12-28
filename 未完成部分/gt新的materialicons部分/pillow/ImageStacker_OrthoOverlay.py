import io

from PIL import Image, ImageChops
from PIL.Image import Resampling
from PIL.ImageFile import ImageFile

from ImageReader import ImageReader
from ImageSegmenter import ImageSegmenter


class ImageStackerOrthoOverlay:
    def __init__(self, bottoms: list[io.BytesIO], joins: list[io.BytesIO]):
        """
        初始化 ImageStackerOrthoOverlay。

        :param bottoms: 底图列表，每个为 io.BytesIO 对象。
        :param joins: 需要叠加的图像列表，每个为 io.BytesIO 对象。
        """
        self.bottoms = self._load_images(bottoms)
        self.joins = self._load_images(joins)
        self.result: Image.Image = None  # 存储最终合并的图像

    @staticmethod
    def _load_images(image_streams: list[io.BytesIO]) -> list[Image.Image]:
        """
        从 io.BytesIO 对象加载 Pillow 图像。

        :param image_streams: io.BytesIO 对象列表。
        :return: 加载后的 Image.Image 对象列表。
        """
        images = []
        for i, stream in enumerate(image_streams):
            try:
                images.append(Image.open(stream))
            except Exception as e:
                print(f"警告：无法加载第 {i} 个图像流: {e}")
        return images

    def apply_overlay_to_bottoms(self):
        """
        对每个底图 (bottom) 按照 joins 的顺序进行正片叠底，并更新 bottoms 列表。
        """
        if not self.bottoms or not self.joins:
            print("错误：底图列表或叠加图像列表为空。")
            return

        for i, bottom in enumerate(self.bottoms):
            result = bottom.copy()  # 创建底图的副本
            for j, join in enumerate(self.joins):
                # 检查尺寸一致性
                if result.size != join.size:
                    print(f"警告：第 {i} 个底图与第 {j} 个叠加图像尺寸不一致，调整尺寸。")
                    try:
                        join = join.resize(result.size, Resampling.NEAREST)
                    except Exception as e:
                        print(f"错误：调整尺寸时出错: {e}")
                        continue

                # 尝试正片叠底
                try:
                    result = ImageChops.multiply(result, join)
                except Exception as e:
                    print(f"错误：正片叠底失败，底图 {i} 与叠加图像 {j}: {e}")
                    continue

            # 更新底图为叠加结果
            self.bottoms[i] = result

        print("所有图像处理完成。")

    def merge_bottoms_vertically(self):
        """
        将处理后的 bottoms 按顺序从上到下拼接成一张完整图像。
        """
        if not self.bottoms:
            print("没有底图可用来合并。")
            return

        # 计算最终图像的宽度和高度
        width = max(bottom.size[0] for bottom in self.bottoms)
        total_height = sum(bottom.size[1] for bottom in self.bottoms)

        # 创建空白图像用于拼接
        final_image = Image.new("RGBA", (width, total_height))
        current_height = 0

        # 按顺序将每个底图粘贴到最终图像中
        for bottom in self.bottoms:
            final_image.paste(bottom, (0, current_height))
            current_height += bottom.size[1]

        self.result = final_image

    def save_result_to_bytes(self) -> io.BytesIO:
        """
        将结果保存为 io.BytesIO 对象。

        :return: 包含结果图像的 io.BytesIO 对象。
        """
        if self.result is None:
            print("错误：没有生成结果图像。")
            return None

        output_stream = io.BytesIO()
        self.result.save(output_stream, format="PNG")
        output_stream.seek(0)  # 重置流位置以供读取
        return output_stream