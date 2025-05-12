# PaddlePaddle OCR 文本识别测试

本项目使用 PaddleOCR 进行图片中的文本识别，并在图片上圈出识别到的文本框和文字。

本项目是AI写的，前后用了20多分钟。

## 环境初始化

请按照以下步骤设置您的 Python 环境：

1.  **创建 Conda 环境** (推荐使用 Python 3.8)
    ```bash
    conda create --name paddle_env python=3.8
    ```

2.  **激活 Conda 环境**
    ```bash
    conda activate paddle_env
    ```

3.  **安装必要的 Python 包**
    ```bash
    pip install paddlepaddle
    pip install paddleocr opencv-python
    ```

## 模型与字体下载

运行脚本前，您需要下载 PaddleOCR 的预训练模型和用于显示中文的字体文件。

1.  **下载 OCR 模型:**
    *   请访问 [PaddleOCR 模型列表](https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.6/doc/doc_ch/models_list.md#21-%E4%B8%AD%E6%96%87%E8%AF%86%E5%88%AB%E6%A8%A1%E5%9E%8B) 下载所需的中文识别模型（例如 `ch_PP-OCRv3` 系列的检测、方向分类和识别模型）。
    *   将下载的模型解压后，放置到项目根目录下的相应文件夹中。脚本 `ocrtest.py` 中默认的模型路径为：
        *   检测模型: `./ch_PP-OCRv3_det_infer/`
        *   方向分类模型: `./ch_ppocr_mobile_v2.0_cls_infer/`
        *   识别模型: `./ch_PP-OCRv3_rec_infer/`
    *   如果您的模型路径不同，请修改 `ocrtest.py` 脚本中的 `DET_MODEL_DIR`, `CLS_MODEL_DIR`, `REC_MODEL_DIR` 变量。

2.  **下载字体文件:**
    *   为了在输出图片上正确显示中文字符，需要一个中文字体文件。
    *   请访问 [PaddleOCR 字体目录](https://github.com/PaddlePaddle/PaddleOCR/tree/main/doc/fonts) 下载字体文件，例如 `simfang.ttf`。
    *   在项目根目录下创建一个名为 `fonts` 的文件夹，并将下载的字体文件（例如 `simfang.ttf`）放入其中。
    *   脚本 `ocrtest.py` 中默认的字体路径为 `./fonts/simfang.ttf`。如果您的字体路径不同，请修改脚本中的 `font_path` 变量。

## 如何运行

1.  **准备图片:** 将需要识别的图片（例如 `your_image.png`）放置在项目可访问的路径下。

2.  **执行脚本:**
    在激活了 `paddle_env` 环境的终端中，运行以下命令：
    ```bash
    python ocrtest.py <你的图片路径>
    ```
    例如:
    ```bash
    python ocrtest.py ./my_image.png
    ```
    或者，如果您有一张名为 `Scan_0002.jpg` 的图片在名为 `438` 的文件夹下：
    ```bash
    python ocrtest.py ./438/Scan_0002.jpg
    ```

3.  **查看结果:**
    *   脚本会在终端打印原始 OCR 结果和处理后的文本行。
    *   一张名为 `result_visualization.jpg` 的图片会保存在项目根目录，其中包含了带有边界框和识别文本的原始图片。
    *   同时，该可视化图片也会在一个窗口中显示，按任意键关闭。
