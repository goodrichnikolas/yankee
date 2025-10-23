"""
The purpose of ad_generation is to systematically create ads of every size and to save them in a sub folder
"""

import os
import glob
import re
import logging
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Change to logging.DEBUG for more detailed output
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

ad_sizes = [
    (300, 250),
    (728, 90),
    (160, 600),
    (320, 50),
    (300, 600),
    (336, 280),
    (970, 250),
    (250, 250),
    (120, 600),
    (468, 60),
    (234, 60),
    (120, 240),
]

ad_text = [
    "Buy Now!",
    "Limited Time Offer!",
    "Best Prices Guaranteed!",]

font_sizes = [16, 20, 24]


def sanitize_filename(text, max_length=8):
    """Convert text to filename-safe format using first 8 non-special characters."""
    # Remove special characters and convert to lowercase
    cleaned = re.sub(r'[^a-zA-Z0-9]', '', text).lower()
    # Take first max_length characters
    return cleaned[:max_length]


def add_text_to_image(img, text, position='middle', font_size=8, offset=5):
    """
    Add text to an image with white color and black border, with word wrapping.

    Args:
        img: PIL Image object
        text: Text to add
        position: 'top', 'middle', or 'bottom'
        font_size: Font size (default 8)
        offset: Offset from edge in pixels (default 5)

    Returns:
        PIL Image with text added
    """
    # Create a copy to avoid modifying original
    img_copy = img.copy()
    draw = ImageDraw.Draw(img_copy)

    # Try to load Comic Sans, fallback to other fonts
    font = None
    font_paths = [
        "comic.ttf",
        "ComicSansMS.ttf",
        "comic.ttc",
        "/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Supplemental/Comic Sans MS.ttf",
        "C:\\Windows\\Fonts\\comic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]

    for font_path in font_paths:
        try:
            font = ImageFont.truetype(font_path, font_size)
            logging.debug(f"Loaded font: {font_path} at size {font_size}")
            break
        except:
            continue

    # Last resort: try to get a default truetype font with size
    if font is None:
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
            logging.debug(f"Loaded fallback arial.ttf at size {font_size}")
        except:
            # Use default font (won't scale properly but better than crashing)
            logging.warning(f"Using default font, size parameter ignored")
            font = ImageFont.load_default()

    # Get image dimensions
    img_width, img_height = img_copy.size

    # Word wrap the text
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        test_width = bbox[2] - bbox[0]

        if test_width <= img_width - (offset * 2):
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Single word is too long, add it anyway
                lines.append(word)

    if current_line:
        lines.append(' '.join(current_line))

    # Calculate total height of all lines
    line_height = draw.textbbox((0, 0), "Ay", font=font)[3] - draw.textbbox((0, 0), "Ay", font=font)[1]
    total_height = line_height * len(lines)

    # Calculate starting y position
    if position == 'top':
        y_start = offset
    elif position == 'bottom':
        y_start = img_height - total_height - offset
    else:  # middle
        y_start = (img_height - total_height) // 2

    # Draw each line
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        x = (img_width - line_width) // 2
        y = y_start + (i * line_height)

        # Draw black border (outline)
        for adj_x in [-1, 0, 1]:
            for adj_y in [-1, 0, 1]:
                if adj_x != 0 or adj_y != 0:
                    draw.text((x + adj_x, y + adj_y), line, font=font, fill='black')

        # Draw white text on top
        draw.text((x, y), line, font=font, fill='white')

    return img_copy


def generate_ad_crops(base_images_dir, output_base_dir, max_dimension=970, step_size=50):
    """
    Generate ad crops from base images by resizing and creating sliding window crops.

    Args:
        base_images_dir: Directory containing base images
        output_base_dir: Directory to save generated ad crops
        max_dimension: Maximum dimension for resizing (default 970)
        step_size: Pixels to move crop window each iteration (default 50)
    """
    # Find all images under base_images
    base_image_paths = glob.glob(os.path.join(base_images_dir, "*.jpg"))

    if not base_image_paths:
        logging.warning(f"No images found in {base_images_dir}")
        return

    logging.info(f"Found {len(base_image_paths)} images to process")

    # Process each image
    for img_path in tqdm(base_image_paths, desc="Processing images", unit="image"):
        try:
            # Open the image
            img = Image.open(img_path)
            original_width, original_height = img.size

            # Get image name without extension
            image_name = os.path.splitext(os.path.basename(img_path))[0]

            # Determine orientation and resize accordingly
            if original_height > original_width:
                # Portrait: resize based on height
                aspect_ratio = original_width / original_height
                new_height = max_dimension
                new_width = int(max_dimension * aspect_ratio)
                resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                logging.info(f"{image_name}: Portrait {original_width}x{original_height} -> {new_width}x{new_height}")
            elif original_width > original_height:
                # Landscape: resize based on width
                aspect_ratio = original_height / original_width
                new_width = max_dimension
                new_height = int(max_dimension * aspect_ratio)
                resized_img = img.resize((new_width, new_height), Image.LANCZOS)
                logging.info(f"{image_name}: Landscape {original_width}x{original_height} -> {new_width}x{new_height}")
            else:
                # Square: leave as-is
                resized_img = img
                new_width, new_height = original_width, original_height
                logging.info(f"{image_name}: Square {original_width}x{original_height} - keeping original size")

            # Create output directory for this image
            image_output_dir = os.path.join(output_base_dir, image_name)
            os.makedirs(image_output_dir, exist_ok=True)

            # For each ad size, create sliding window crops
            for ad_width, ad_height in tqdm(ad_sizes, desc=f"  Ad sizes for {image_name}", leave=False, unit="size"):
                # Skip if ad size is larger than the resized image
                if ad_width > new_width or ad_height > new_height:
                    logging.debug(f"Skipping {ad_width}x{ad_height} for {image_name} - too large for image")
                    continue

                # Calculate total number of crops for progress bar
                y_positions = list(range(0, new_height - ad_height + 1, step_size))
                x_positions = list(range(0, new_width - ad_width + 1, step_size))
                total_crops = len(y_positions) * len(x_positions)

                crop_index = 0

                # Create progress bar for crops
                with tqdm(total=total_crops, desc=f"    Crops {ad_width}x{ad_height}", leave=False, unit="crop") as pbar:
                    # Slide vertically
                    for y in y_positions:
                        # Slide horizontally
                        for x in x_positions:
                            # Crop the image
                            crop_box = (x, y, x + ad_width, y + ad_height)
                            cropped_img = resized_img.crop(crop_box)

                            # Create folder for this crop
                            crop_folder_name = f"{ad_width}x{ad_height}_{crop_index}"
                            crop_folder_path = os.path.join(image_output_dir, crop_folder_name)
                            os.makedirs(crop_folder_path, exist_ok=True)

                            # Save preview image of the crop without text
                            preview_filename = f"{ad_width}x{ad_height}_{crop_index}.jpg"
                            preview_path = os.path.join(crop_folder_path, preview_filename)
                            cropped_img.save(preview_path, quality=95)
                            logging.debug(f"Saved preview: {preview_filename}")

                            # Generate all font size, text, and position combinations
                            for font_size in font_sizes:
                                # Create subfolder for font size
                                font_size_folder = os.path.join(crop_folder_path, str(font_size))
                                os.makedirs(font_size_folder, exist_ok=True)

                                for text in ad_text:
                                    text_slug = sanitize_filename(text)
                                    for position in ['top', 'middle', 'bottom']:
                                        # Add text to the cropped image
                                        img_with_text = add_text_to_image(cropped_img, text, position, font_size)

                                        # Save the image
                                        filename = f"{text_slug}_{position}.jpg"
                                        file_path = os.path.join(font_size_folder, filename)
                                        img_with_text.save(file_path, quality=95)

                            crop_index += 1
                            pbar.update(1)

                total_variations = crop_index * len(font_sizes) * len(ad_text) * 3  # font sizes × texts × 3 positions
                logging.info(f"Generated {crop_index} crops for {image_name} {ad_width}x{ad_height} ({total_variations} total variations)")

        except Exception as e:
            logging.error(f"Error processing {img_path}: {e}", exc_info=True)


def main():
    """Main entry point for ad generation."""
    logging.info("Starting ad generation process")

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    base_images_dir = os.path.join(script_dir, "base_images")
    output_base_dir = os.path.join(script_dir, "generated_ads")

    # Generate ad crops
    generate_ad_crops(base_images_dir, output_base_dir, max_dimension=970, step_size=50)

    logging.info("Ad generation complete!")


if __name__ == "__main__":
    main()