import warnings
import logging
import sys
# Suppress the specific UserWarning from PaddlePaddle about ccache
warnings.filterwarnings("ignore", category=UserWarning, module='paddle.utils.cpp_extension.extension_utils')

import cv2
from paddleocr import PaddleOCR, draw_ocr
from paddleocr import PPStructure, save_structure_res

# Set ppocr logger level to INFO to suppress DEBUG messages
logging.getLogger('ppocr').setLevel(logging.INFO)

# 1. 指定模型目录（请先从 https://github.com/PaddlePaddle/PaddleOCR 中的 ModelZoo 下载 ch_ppocr v3 模型到本地）
DET_MODEL_DIR = "./ch_PP-OCRv3_det_infer"   # 检测模型
CLS_MODEL_DIR = "./ch_ppocr_mobile_v2.0_cls_infer"  # 方向分类模型
REC_MODEL_DIR = "./ch_PP-OCRv3_rec_infer"  # 识别模型

TABLE_MODEL_DIR="./ch_ppstructure_mobile_v2.0_SLANet_infer"
# 字典文件（PPOCRKeys + Table Structure Dict）
REC_CHAR_DICT_PATH="./ppocr_keys_v1.txt"
TABLE_CHAR_DICT_PATH="./table_structure_dict.txt"

# read image_path from sys argv
image_path = sys.argv[1]

# 2. 初始化 OCR 引擎，强制使用中文
ocr = PaddleOCR(
    det_model_dir=DET_MODEL_DIR,
    cls_model_dir=CLS_MODEL_DIR,
    rec_model_dir=REC_MODEL_DIR,
    use_angle_cls=True,   # 启用文字方向分类
    lang="ch"             # 仅加载中文识别
)

# Define a helper function to recursively extract OCR line data
def get_ocr_lines(data):
    lines = []
    if isinstance(data, list):
        # Heuristic check: if the first element of 'data' looks like an OCR line item,
        # assume 'data' is the list of OCR line items we are looking for.
        # An OCR line item is typically [bbox, (text, score)]
        # where bbox is List[List[float/int]] and (text, score) is Tuple[str, float]
        is_direct_list_of_lines = False
        if data: # Check if data is not empty
            first_item = data[0]
            if (isinstance(first_item, list) and len(first_item) == 2 and
                    isinstance(first_item[0], list) and  # bbox
                    (first_item[0] and isinstance(first_item[0][0], list)) and # first point in bbox
                    (first_item[0][0] and (isinstance(first_item[0][0][0], float) or isinstance(first_item[0][0][0], int))) and # x-coordinate
                    isinstance(first_item[1], tuple) and len(first_item[1]) == 2 and  # (text, score) tuple
                    isinstance(first_item[1][0], str) and isinstance(first_item[1][1], float)):
                is_direct_list_of_lines = True
                # Further check if all items in data follow this pattern (optional for brevity here, but good for robustness)

        if is_direct_list_of_lines:
            return data # This list 'data' is the list of OCR lines
        else:
            # If not a direct list of lines, assume it's a list of sub-lists and recurse
            for sub_list in data:
                lines.extend(get_ocr_lines(sub_list))
    return lines

# Define path for font file (needed for drawing Chinese characters)
# You might need to change this path based on where you have simfang.ttf or another suitable font
font_path = './fonts/simfang.ttf'

# 3. 读取图片（也可以传入 numpy 数组）
img = cv2.imread(image_path)

# 4. 执行 OCR
results = ocr.ocr(img, cls=True)
print("Raw OCR results:")
print(results)

# Extract boxes, texts, and scores for draw_ocr
boxes = None
txts = None
scores = None
# Check if results is not None, not empty, and results[0] is not empty
if results and results[0]:
    processed_results = results[0]
    try:
        boxes = [line[0] for line in processed_results]  # List of bounding boxes
        txts = [line[1][0] for line in processed_results]   # List of text strings
        scores = [line[1][1] for line in processed_results] # List of scores
    except (IndexError, TypeError) as e:
        print(f"Error extracting data from results: {e}. Results format might be unexpected.")
        # Keep boxes, txts, scores as None

# --- Visualization using draw_ocr ---
# Ensure the font file exists before trying to draw
import os
if not os.path.exists(font_path):
    print(f"\nWarning: Font file not found at {font_path}. Text rendering in the output image might be incorrect.")
    print("Please download a suitable font (like simfang.ttf) and place it at the specified path or update the font_path variable.")
    # Draw without text if font is missing (optional, draw_ocr might handle it)
    # Or exit/skip drawing if font is critical
    # Pass separated 'boxes' list to draw_ocr
    if boxes: # Check if boxes were successfully extracted
        image_with_boxes = draw_ocr(img, boxes, txts=None, scores=None, font_path=None)
    else:
        print("Error: Could not draw boxes as they were not extracted successfully.")
        image_with_boxes = img.copy() # Use original image if extraction failed

else:
    # Draw boxes and text onto the image
    # Pass separated 'boxes', 'txts', 'scores' lists to draw_ocr
    if boxes and txts and scores: # Check if all components were extracted
         image_with_boxes = draw_ocr(img, boxes, txts=txts, scores=scores, font_path=font_path)
    else:
        print("Error: Could not draw visualization as boxes, texts, or scores were not extracted successfully.")
        image_with_boxes = img.copy() # Use original image if extraction failed

# Save the visualized image
output_image_path = './result_visualization.jpg'
cv2.imwrite(output_image_path, image_with_boxes)
print(f"\nVisualization saved to: {output_image_path}")

# Display the image
is_display_debug = False
if is_display_debug:
    cv2.imshow('OCR Result Visualization', image_with_boxes)
    print("Press any key in the image window to close it.")
    cv2.waitKey(0)  # Wait indefinitely until a key is pressed
    cv2.destroyAllWindows() # Close the image window

# -------------------------------------

# 5. 打印识别结果
all_detected_lines = get_ocr_lines(results)

if not all_detected_lines:
    print("\nNo text detected or results format not recognized after processing.")
else:
    print(f"\nProcessed {len(all_detected_lines)} lines of text:")
    for i, line_data in enumerate(all_detected_lines):
        # Defensive check for the expected structure of a line_data item
        if isinstance(line_data, list) and len(line_data) == 2:
            bbox, text_score_pair = line_data
            if isinstance(text_score_pair, tuple) and len(text_score_pair) == 2:
                text, score = text_score_pair
                print(f"Line {i+1}: {text}    # Confidence: {score:.3f}")
                # You might also want to print or use the bounding box (bbox) here if needed.
                # print(f"  Bounding Box: {bbox}")
            else:
                print(f"Warning: Malformed text_score_pair in line_data item {i+1}: {text_score_pair}")
        else:
            print(f"Warning: Malformed line_data item {i+1}: {line_data}")

# 6. 初始化 PP-Structure 引擎
engine = PPStructure(
    det_model_dir=DET_MODEL_DIR,
    rec_model_dir=REC_MODEL_DIR,
    table_model_dir=TABLE_MODEL_DIR,
    rec_char_dict_path=REC_CHAR_DICT_PATH,
    table_char_dict_path=TABLE_CHAR_DICT_PATH,
    lang="ch"   # 中文环境
)

# 7. 读取图片并预测
img = cv2.imread(image_path)
results = engine(img)  # 返回一个 dict 列表，包含 Text/Table/Title 等多种 type

# 8. 导出结果
for res in results:
    # 保存 Excel
    save_structure_res(results, "./output", "mytable")
    # 或者保存 JSON
    save_structure_res(results, "./output", "mytable", output_format="json")
    break  # 多图按需循环

print("Done.")