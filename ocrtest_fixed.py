import warnings
import logging
import sys
import os
import cv2
import json
import argparse
import csv
from PIL import Image
import numpy as np

# Suppress the specific UserWarning from PaddlePaddle about ccache
warnings.filterwarnings("ignore", category=UserWarning, module='paddle.utils.cpp_extension.extension_utils')

from paddleocr import PaddleOCR, draw_ocr

# Set ppocr logger level to INFO to suppress DEBUG messages
logging.getLogger('ppocr').setLevel(logging.INFO)

# Model paths
DET_MODEL_DIR = "./ch_PP-OCRv3_det_infer"   # 检测模型
CLS_MODEL_DIR = "./ch_ppocr_mobile_v2.0_cls_infer"  # 方向分类模型
REC_MODEL_DIR = "./ch_PP-OCRv3_rec_infer"  # 识别模型

# Initialize PaddleOCR
ocr_engine = None

def initialize_ocr(det_model_dir, cls_model_dir, rec_model_dir, use_angle_cls=True, lang='ch'):
    """Initializes and returns the PaddleOCR engine."""
    global ocr_engine
    ocr_engine = PaddleOCR(use_angle_cls=use_angle_cls,
                         lang=lang,
                         det_model_dir=det_model_dir,
                         cls_model_dir=cls_model_dir,
                         rec_model_dir=rec_model_dir,
                         show_log=False, # Suppress detailed OCR logs for cleaner output
                         use_gpu=False) # Set to True if GPU is available and desired
    print("PaddleOCR engine initialized.")

def process_image_fixed_grid(image_path, output_csv_path, row_height, col_widths):
    """
    Processes an image with a fixed grid, performs OCR on each cell, and saves to CSV.
    """
    global ocr_engine
    if ocr_engine is None:
        print("Error: OCR engine not initialized. Call initialize_ocr first.")
        return

    try:
        img = Image.open(image_path).convert('RGB') # Ensure image is in RGB
        img_np = np.array(img) # PaddleOCR prefers numpy array
        image_height_pil, image_width_pil = img.height, img.width # PIL uses (width, height) from size, np uses (height, width)

    except FileNotFoundError:
        print(f"Error: Input image not found at {image_path}")
        return
    except Exception as e:
        print(f"Error loading image: {e}")
        return

    table_data = []
    current_y = 0
    row_idx = 0

    print(f"Processing image: {image_path} (Dimensions: {image_width_pil}x{image_height_pil})")
    print(f"Row height: {row_height}, Column widths: {col_widths}")

    while current_y + row_height <= image_height_pil:
        row_data = []
        current_x = 0
        col_idx = 0
        for col_width in col_widths:
            if current_x + col_width <= image_width_pil:
                # Define the crop box for PIL [left, upper, right, lower]
                # For numpy slicing it's [y1:y2, x1:x2]
                cell_np = img_np[current_y : current_y + row_height, current_x : current_x + col_width]
                
                if cell_np.size == 0:
                    print(f"Warning: Empty cell crop at R{row_idx}C{col_idx} (x:{current_x}, y:{current_y}, w:{col_width}, h:{row_height}). Skipping.")
                    text_results = ""
                else:
                    try:
                        result = ocr_engine.ocr(cell_np, cls=True) # cls for orientation correction if needed
                        cell_text_parts = []
                        if result and result[0]: # Check if result is not None and not empty
                            for line_info in result[0]: # Iterate over lines found in the cell
                                cell_text_parts.append(line_info[1][0]) # Append the text part
                        text_results = " ".join(cell_text_parts) # Join multiple text parts if any
                    except Exception as e:
                        print(f"Error during OCR for cell R{row_idx}C{col_idx}: {e}")
                        text_results = "<OCR_ERROR>"
                
                row_data.append(text_results)
                # print(f"  Cell R{row_idx}C{col_idx} (x:{current_x}, y:{current_y}, w:{col_width}, h:{row_height}) -> '{text_results[:30]}...' ")
            else:
                # print(f"Warning: Column width {col_width} exceeds image width at x={current_x} for row {row_idx}. Stopping row.")
                row_data.append("<OUT_OF_BOUNDS>") # Or empty string, or skip
                break # Stop processing this row if a column goes out of bounds
            current_x += col_width
            col_idx += 1
        
        if row_data:
            table_data.append(row_data)
        else:
            # This case should ideally not be hit if loop conditions are right
            print(f"Warning: No data processed for row at y={current_y}.")
            break

        current_y += row_height
        row_idx += 1
        if row_idx % 10 == 0:
            print(f"Processed {row_idx} rows...")

    print(f"\nFinished processing. Total rows extracted: {len(table_data)}")

    # Save to CSV
    try:
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(table_data)
        print(f"Successfully saved CSV to {output_csv_path}")
    except Exception as e:
        print(f"Error saving CSV: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OCR fixed-grid table images and output to CSV.")
    parser.add_argument("image_path", type=str, help="Path to the input image file.")
    parser.add_argument("output_csv", type=str, help="Path to save the output CSV file.")
    parser.add_argument("--row_height", type=int, default=24, help="Fixed height of each row (default: 24).")
    parser.add_argument("--col_widths", type=str, default="81,80,82,80,82,81,81,81,82",
                        help='Comma-separated list of fixed column widths (default: "95,67,97,74,92,65,82,106,51").')
    
    # Optional: Add arguments for model paths if they shouldn't be hardcoded
    parser.add_argument("--det_model", type=str, default=DET_MODEL_DIR, help="Path to detection model directory.")
    parser.add_argument("--cls_model", type=str, default=CLS_MODEL_DIR, help="Path to classification model directory.")
    parser.add_argument("--rec_model", type=str, default=REC_MODEL_DIR, help="Path to recognition model directory.")
    parser.add_argument("--lang", type=str, default='ch', help="OCR language (default: 'ch').")
    parser.add_argument("--use_angle_cls", type=bool, default=True, help="Use angle classification (default: True).")


    args = parser.parse_args()

    try:
        parsed_col_widths = [int(w.strip()) for w in args.col_widths.split(',') if w.strip()]
        if not parsed_col_widths:
            raise ValueError("Column widths cannot be empty.")
    except ValueError as e:
        print(f"Error: Invalid format for column widths. Please use comma-separated integers. Details: {e}")
        sys.exit(1)

    # Initialize OCR engine (using paths from args or defaults)
    initialize_ocr(args.det_model, args.cls_model, args.rec_model, args.use_angle_cls, args.lang)

    process_image_fixed_grid(args.image_path, args.output_csv, args.row_height, parsed_col_widths)