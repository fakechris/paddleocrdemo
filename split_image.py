import os
from PIL import Image
import argparse

def split_image(image_path, output_dir, target_sub_height=800):
    """
    Splits an image into multiple sub-images of a target height.

    Args:
        image_path (str): Path to the input image.
        output_dir (str): Directory to save the sub-images.
        target_sub_height (int): The target height for each sub-image.
                                 The actual height can be between 700-900 as per user requirement,
                                 for now, we use a fixed target. The last piece might be shorter.
    """
    try:
        img = Image.open(image_path)
        img_width, img_height = img.size

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")

        current_y = 0
        sub_image_count = 0

        while current_y < img_height:
            # Define the crop box [left, upper, right, lower]
            # Width will be the original image width (e.g., 730)
            # Height will be target_sub_height, or less for the last piece
            box_upper = current_y
            box_lower = min(current_y + target_sub_height, img_height)
            
            # Ensure the piece is not too small (e.g., less than 10 pixels) unless it's all that's left
            if img_height - current_y < 10 and current_y != 0: # Avoid creating tiny slivers if not the only piece
                 # If the remaining part is very small, consider attaching to the previous one or skipping.
                 # For now, we'll just crop what's left.
                 pass 

            if box_lower - box_upper <= 0: # Should not happen if logic is correct
                break

            crop_box = (0, box_upper, img_width, box_lower)
            sub_image = img.crop(crop_box)
            
            sub_image_filename = f"sub_image_{sub_image_count:03d}.png"
            sub_image_path = os.path.join(output_dir, sub_image_filename)
            sub_image.save(sub_image_path)
            print(f"Saved: {sub_image_path} (Dimensions: {sub_image.width}x{sub_image.height})")
            
            sub_image_count += 1
            current_y += target_sub_height

        print(f"\nSuccessfully split {image_path} into {sub_image_count} sub-images in {output_dir}")

    except FileNotFoundError:
        print(f"Error: Input image not found at {image_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split a large image into multiple sub-images.")
    parser.add_argument("image_path", type=str, help="Path to the input image file.")
    parser.add_argument("output_dir", type=str, help="Directory to save the split sub-images.")
    parser.add_argument("--height", type=int, default=800, 
                        help="Target height for each sub-image (default: 800). User wants 700-900.")

    args = parser.parse_args()

    # Validate target height to be within reasonable bounds if specified
    # For now, we allow any positive height, but ideally check 700-900 range if strictly needed.
    if args.height <= 0:
        print("Error: Target height must be a positive integer.")
    else:
        split_image(args.image_path, args.output_dir, args.height)
