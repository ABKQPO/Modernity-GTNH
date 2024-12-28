import os

from ImageReader import ImageReader
from ImageSegmenter import ImageSegmenter
from ImageStacker_OrthoOverlay import ImageStackerOrthoOverlay


class Scripts:
    def __init__(self):
        self.targets = input("输入目标图像文件夹路径:")
        self.overlays = input("输入覆盖图像文件夹路径:")
        self.savePath = input("输入保存路径:")

        self.targetImages = []
        self.overlayImages = []

        self._readImages()

    def _readImages(self):
        self.targetImages = ImageReader(self.targets).images
        self.overlayImages = ImageReader(self.overlays).images

    # 遍历覆盖图像，根据覆盖图像名称减去.png创建一个文件夹在savePath中，然后使用ImageSegmenter进行分割
    # 再遍历targets，对其同样使用ImageSegmenter分割
    # 再使用ImageStackerOrthoOverlay对每个target进行图像合成，最后将结果使用target的名称保存到创建的分支文件夹中
    def process_images(self):
        """根据逻辑对图像进行分割、叠加并保存结果。"""
        for overlay_path in self.overlayImages:
            overlay_name = os.path.basename(overlay_path).replace(".png", "")
            overlay_save_dir = os.path.join(self.savePath, overlay_name)

            # 创建覆盖图像对应的文件夹
            os.makedirs(overlay_save_dir, exist_ok=True)

            for target_path in self.targetImages:
                # 分割覆盖图像
                overlay_segments = ImageSegmenter(overlay_path).images
                target_name = os.path.basename(target_path)

                # 分割目标图像
                target_segments = ImageSegmenter(target_path).images

                # 合成图像
                stacker = ImageStackerOrthoOverlay(overlay_segments, target_segments)
                stacker.apply_overlay_to_bottoms()
                stacker.merge_bottoms_vertically()

                # 保存合成结果
                result_path = os.path.join(overlay_save_dir, target_name)
                stacker.result.save(result_path)

                print(f"保存合成图像到: {result_path}")

if __name__ == "__main__":
    scripts = Scripts()
    scripts.process_images()