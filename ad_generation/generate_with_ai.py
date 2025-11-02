#!/usr/bin/env python3
"""
Generate ad images in all standard sizes from a single prompt.
Creates a folder for each prompt and generates the same image in different dimensions.
"""

import sys
import os
import glob
from datetime import datetime
import torch
from PIL import Image

# Add the ai-image-gen path to import the generator
sys.path.insert(0, '/home/nikolas/projects/ai-image-gen')
from generate_civitai import CivitAIGenerator

# ========== CONFIGURATION - Update these parameters ==========

# Model path (required)
# Supports both SD 1.5 and SDXL models - auto-detects based on file size
# NOTE: Must be a FULL checkpoint, not a LoRA or partial weights
MODEL_PATH = "/home/nikolas/projects/ai-image-gen/models/jibMixRealisticSD15_v10.safetensors"

# Generation parameters
PROMPT = "50 year old woman with silver hair spreads her ass showing her pink butthole"
NEGATIVE_PROMPT = "blurry, low quality, distorted, text, watermark, ugly, bad anatomy"

# Generation settings
NUM_INFERENCE_STEPS = 75
GUIDANCE_SCALE = 7.5
SEED = None  # Set to a number for reproducible results, or None for random

# Output
BASE_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "base_images")

# Optional: Image-to-image mode
INIT_IMAGE = None  # Path to starter image, or None for text-to-image
STRENGTH = 0.75  # How much to transform the init image (0.0-1.0)

# Optional: LoRA
LORA_PATH = "/home/nikolas/projects/ai-image-gen/models/skin_texture.safetensors"
LORA_WEIGHT = 0.8  # LoRA strength (0.0-1.0)

# Animated GIF settings
GIF_NUM_FRAMES = 40  # Number of frames in panning animation
GIF_FRAME_DURATION = 300  # Milliseconds per frame (100ms = 0.1s)

# ==============================================================

# Standard ad sizes (adjusted to be divisible by 8 for Stable Diffusion)
AD_SIZES = {
    # Desktop Ads
    "desktop": {
        "medium_rectangle": (304, 248),      # Standard: 300 × 250
        "leaderboard": (728, 88),             # Standard: 728 × 90
        "wide_skyscraper": (160, 600),        # Standard: 160 × 600
        "half_page": (304, 600),              # Standard: 300 × 600
        "large_rectangle": (336, 280),        # Standard: 336 × 280
        "billboard": (968, 248),              # Standard: 970 × 250
        "large_leaderboard": (968, 88),       # Standard: 970 × 90
        "square": (248, 248),                 # Standard: 250 × 250
    },
    # Mobile Ads
    "mobile": {
        "mobile_leaderboard": (320, 48),      # Standard: 320 × 50
        "large_mobile_banner": (320, 104),    # Standard: 320 × 100
        "small_square": (200, 200),           # Standard: 200 × 200
        "interstitial_portrait": (320, 480),  # Standard: 320 × 480
        "interstitial_landscape": (480, 320), # Standard: 480 × 320
    }
}


def make_folder_name(prompt, seed):
    """Create a safe folder name from prompt and seed"""
    # Take first 50 chars of prompt, replace spaces and special chars
    safe_prompt = "".join(c if c.isalnum() else "_" for c in prompt[:50])
    safe_prompt = safe_prompt.strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{safe_prompt}_seed{seed}"


def crop_and_resize_to_ad_size(image, target_width, target_height):
    """
    Crop image to target aspect ratio (center crop) then resize to exact dimensions.
    This preserves the subject while avoiding distortion.
    """
    img_width, img_height = image.size
    target_aspect = target_width / target_height
    current_aspect = img_width / img_height

    # Crop to target aspect ratio first
    if current_aspect > target_aspect:
        # Image is wider than target - crop width
        new_width = int(img_height * target_aspect)
        left = (img_width - new_width) // 2
        cropped = image.crop((left, 0, left + new_width, img_height))
    elif current_aspect < target_aspect:
        # Image is taller than target - crop height
        new_height = int(img_width / target_aspect)
        top = (img_height - new_height) // 2
        cropped = image.crop((0, top, img_width, top + new_height))
    else:
        # Aspect ratios match
        cropped = image

    # Resize to exact target dimensions
    resized = cropped.resize((target_width, target_height), Image.LANCZOS)
    return resized


def create_panning_gif(image, target_width, target_height, output_path, num_frames=20, duration=100):
    """
    Create an animated GIF that pans across the master image.
    - If wider than tall: pan top to bottom
    - If taller than wide: pan left to right
    """
    img_width, img_height = image.size
    target_aspect = target_width / target_height

    frames = []

    if target_width > target_height:
        # Landscape ad: pan top to bottom
        # Calculate crop window size maintaining aspect ratio
        crop_width = img_width
        crop_height = int(crop_width / target_aspect)

        # Can't pan if crop is larger than image
        if crop_height > img_height:
            crop_height = img_height
            crop_width = int(crop_height * target_aspect)

        # Calculate pan range
        max_top = img_height - crop_height

        if max_top > 0:
            # Create frames by moving window top to bottom
            for i in range(num_frames):
                top = int((max_top * i) / (num_frames - 1)) if num_frames > 1 else 0
                left = (img_width - crop_width) // 2

                cropped = image.crop((left, top, left + crop_width, top + crop_height))
                resized = cropped.resize((target_width, target_height), Image.LANCZOS)
                frames.append(resized)
        else:
            # Can't pan, just use center crop
            frames.append(crop_and_resize_to_ad_size(image, target_width, target_height))
    else:
        # Portrait or square ad: pan left to right
        # Calculate crop window size maintaining aspect ratio
        crop_height = img_height
        crop_width = int(crop_height * target_aspect)

        # Can't pan if crop is larger than image
        if crop_width > img_width:
            crop_width = img_width
            crop_height = int(crop_width / target_aspect)

        # Calculate pan range
        max_left = img_width - crop_width

        if max_left > 0:
            # Create frames by moving window left to right
            for i in range(num_frames):
                left = int((max_left * i) / (num_frames - 1)) if num_frames > 1 else 0
                top = (img_height - crop_height) // 2

                cropped = image.crop((left, top, left + crop_width, top + crop_height))
                resized = cropped.resize((target_width, target_height), Image.LANCZOS)
                frames.append(resized)
        else:
            # Can't pan, just use center crop
            frames.append(crop_and_resize_to_ad_size(image, target_width, target_height))

    # Save as animated GIF
    if frames:
        frames[0].save(
            output_path,
            save_all=True,
            append_images=frames[1:],
            duration=duration,
            loop=0,  # Loop forever
            optimize=False
        )


def main():
    # Validate model path
    if not os.path.exists(MODEL_PATH):
        print(f"Error: Model not found at {MODEL_PATH}")
        print("Please update MODEL_PATH in this script to point to your .safetensors model file")
        return 1

    # Generate or use provided seed
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if SEED is None:
        generation_seed = torch.randint(0, 2**32, (1,)).item()
        print(f"Generated random seed: {generation_seed}")
    else:
        generation_seed = SEED
        print(f"Using seed: {generation_seed}")

    # Create output folder for this prompt/seed
    folder_name = make_folder_name(PROMPT, generation_seed)
    output_dir = os.path.join(BASE_OUTPUT_DIR, folder_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nOutput directory: {output_dir}\n")
    print("=" * 80)

    # Create generator
    print("Initializing AI image generator...")
    generator = CivitAIGenerator(
        model_path=MODEL_PATH,
        lora_path=LORA_PATH,
        lora_weight=LORA_WEIGHT
    )

    # Load model
    generator.load_model(
        scheduler="dpm",
        load_img2img=(INIT_IMAGE is not None)
    )

    # Generate ONE master image at 1024x1024
    print("Generating master image at 1024×1024...")
    print(f"Prompt: {PROMPT}")
    print(f"Seed: {generation_seed}\n")

    master_output_dir = os.path.join(output_dir, "_master")
    os.makedirs(master_output_dir, exist_ok=True)

    images = generator.generate(
        prompt=PROMPT,
        negative_prompt=NEGATIVE_PROMPT,
        width=1024,
        height=1024,
        num_inference_steps=NUM_INFERENCE_STEPS,
        guidance_scale=GUIDANCE_SCALE,
        num_images=1,
        seed=generation_seed,
        output_dir=master_output_dir,
        init_image=INIT_IMAGE,
        strength=STRENGTH
    )

    # Find the generated master image
    generated_files = glob.glob(os.path.join(master_output_dir, "*.png"))
    if not generated_files:
        print("Error: Failed to generate master image")
        return 1

    master_image_path = max(generated_files, key=os.path.getctime)
    master_image = Image.open(master_image_path)
    print(f"✓ Master image generated: {master_image_path}\n")

    # Count total sizes
    total_sizes = sum(len(sizes) for sizes in AD_SIZES.values())
    current = 0

    # Create all ad sizes from the master image
    print("=" * 80)
    print("Creating ad variations from master image...")
    print("=" * 80)

    for category, sizes in AD_SIZES.items():
        print(f"\n{category.upper()} ads:")

        for ad_name, (width, height) in sizes.items():
            current += 1
            print(f"  [{current}/{total_sizes}] {ad_name} ({width}×{height})...", end=" ")

            # Create subfolders for this size
            size_output_dir = os.path.join(output_dir, category, ad_name)
            gif_output_dir = os.path.join(output_dir, category, ad_name, "gifs")
            os.makedirs(size_output_dir, exist_ok=True)
            os.makedirs(gif_output_dir, exist_ok=True)

            # Crop and resize from master image (static)
            ad_image = crop_and_resize_to_ad_size(master_image, width, height)

            # Save static image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{size_output_dir}/civitai_{timestamp}_seed{generation_seed}_{ad_name}.png"
            ad_image.save(filename)
            print(f"✓ static", end=" ")

            # Create animated GIF
            pan_direction = "↓" if width > height else "→"
            gif_filename = f"{gif_output_dir}/civitai_{timestamp}_seed{generation_seed}_{ad_name}_pan.gif"
            create_panning_gif(master_image, width, height, gif_filename,
                             num_frames=GIF_NUM_FRAMES, duration=GIF_FRAME_DURATION)
            print(f"✓ gif {pan_direction}")

    print("\n" + "=" * 80)
    print(f"✓ Successfully created {total_sizes} ad sizes from master image!")
    print(f"✓ Each size has: static PNG + animated GIF (panning)")
    print(f"✓ Master image: {master_image_path}")
    print(f"✓ All ads saved to: {output_dir}")
    print("=" * 80)

    # Print summary
    print(f"\nGenerated sizes (all from seed {generation_seed}):")
    print("Each includes: static image + animated GIF (↓ = top-to-bottom, → = left-to-right)")
    for category, sizes in AD_SIZES.items():
        print(f"\n{category.upper()}:")
        for ad_name, (width, height) in sizes.items():
            pan_dir = "↓" if width > height else "→"
            print(f"  • {ad_name}: {width}×{height} {pan_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
