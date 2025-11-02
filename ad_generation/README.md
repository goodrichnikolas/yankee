# Yankee Ad Platform

A complete ad generation, testing, and optimization pipeline for adult content advertising. This platform systematically creates ads, scrapes competitor data, and uses statistical testing to minimize ad spend while maximizing conversions.

## Platform Components

### 1. AI Ad Generation (`generate_with_ai.py`)
Generates advertisement images using Stable Diffusion AI, creating both static and animated ads in all standard sizes.

**Features:**
- Generate master image (1024x1024) from text prompt
- Automatic cropping and resizing to 13 standard ad sizes
- Creates animated GIFs with panning effects (horizontal/vertical)
- Maintains aspect ratios with intelligent center cropping
- Single seed ensures consistency across all sizes

### 2. Manual Ad Generation (`main.py`)
Takes base images and generates variations through systematic cropping and text overlays.

**Features:**
- Resizing images to appropriate dimensions
- Creating sliding window crops for each standard ad size
- Adding text overlays in different positions, fonts, and messages
- Organizing outputs for easy A/B testing and deployment

### 3. Ad Scraper (`../ad_scraper/main.py`)
Scrapes competitor ads from JuicyAds network sites to analyze market trends.

**Features:**
- Automated browser-based scraping with Playwright
- Extracts ads from iframes, ins tags, and common ad containers
- Screenshots ad images and tracks destination URLs
- CSV export of all ad metadata
- Targets 50+ high-traffic JuicyAds sites

### 4. Statistical Testing (`../stats/binomial_test.py`)
Performs binomial tests to determine ad effectiveness and prune underperformers.

**Features:**
- One-sided binomial test for CTR analysis
- Identifies ads significantly below target CTR
- Configurable p-value threshold (default: 0.01)
- Supports minimum impression requirements (5,000+)

## Requirements

### Core Dependencies
```bash
# Manual ad generation
pip install Pillow tqdm

# AI ad generation (requires CUDA GPU for best performance)
pip install torch torchvision diffusers transformers accelerate safetensors

# Ad scraper
pip install playwright asyncio
playwright install chromium

# Statistical testing
pip install scipy
```

See `requirements.txt` for complete dependency list.

## Directory Structure

```
yankee/
├── ad_generation/
│   ├── generate_with_ai.py    # AI-based ad generator
│   ├── main.py                # Manual ad generator
│   ├── base_images/           # Source images (*.jpg)
│   └── generated_ads/         # Output directory
│       └── [timestamp_prompt_seed]/
│           ├── _master/       # Original 1024x1024 generated image
│           ├── desktop/       # Desktop ad sizes
│           │   └── [ad_name]/
│           │       ├── *.png  # Static images
│           │       └── gifs/  # Animated panning GIFs
│           └── mobile/        # Mobile ad sizes
│               └── [ad_name]/
│                   ├── *.png
│                   └── gifs/
├── ad_scraper/
│   ├── main.py                # Competitor ad scraper
│   ├── ad_images/             # Scraped ad screenshots
│   └── ad_screenshots.csv     # Ad metadata
├── stats/
│   └── binomial_test.py       # CTR statistical testing
└── CLAUDE.md                  # Platform guidelines and parameters
```

## Supported Ad Sizes

Both generators support standard IAB ad sizes (dimensions adjusted to be divisible by 8 for AI):

**Desktop Ads:**
- 304x248 (Medium Rectangle - ~300x250)
- 728x88 (Leaderboard - ~728x90)
- 160x600 (Wide Skyscraper)
- 304x600 (Half Page - ~300x600)
- 336x280 (Large Rectangle)
- 968x248 (Billboard - ~970x250)
- 968x88 (Large Leaderboard - ~970x90)
- 248x248 (Square - ~250x250)

**Mobile Ads:**
- 320x48 (Mobile Leaderboard - ~320x50)
- 320x104 (Large Mobile Banner - ~320x100)
- 200x200 (Small Square)
- 320x480 (Interstitial Portrait)
- 480x320 (Interstitial Landscape)

## Quick Start

### AI-Based Generation (Recommended)

1. **Configure the script** - Edit `generate_with_ai.py` (lines 18-46):
```python
MODEL_PATH = "/path/to/your/model.safetensors"
PROMPT = "Your ad image description"
NEGATIVE_PROMPT = "blurry, low quality, distorted"
NUM_INFERENCE_STEPS = 75  # Higher = better quality
GUIDANCE_SCALE = 7.5
```

2. **Run the generator**:
```bash
python generate_with_ai.py
```

3. **Output**: Creates folder with:
   - Master 1024x1024 image
   - 13 ad sizes (static PNGs + animated GIFs)
   - Consistent seed across all sizes

### Ad Scraper

1. **Run the scraper**:
```bash
cd ../ad_scraper
python main.py
```

2. **Output**:
   - `ad_images/` - Screenshots of competitor ads
   - `ad_screenshots.csv` - Ad metadata (source, destination URL, image src)

### Statistical Testing

**Analyze CTR performance**:
```python
from stats.binomial_test import site_ctr_test

result = site_ctr_test(
    clicks=50,
    impressions=10000,
    target_ctr=0.001,  # 0.1%
    alpha=0.01
)

print(result['interpretation'])
# "No evidence CTR is below 0.100% (p=0.9999)" = Keep ad
# "CTR is significantly below 0.100% (p=0.0001)" = Prune ad
```

## Platform Workflow

1. **Generate Ads** - Use `generate_with_ai.py` to create ad variations
2. **Deploy** - Upload to JuicyAds network
3. **Run** - Let ads run minimum 24 hours (covers time windows)
4. **Collect** - Gather impression/click data (minimum 5,000 impressions)
5. **Analyze** - Use `binomial_test.py` to identify underperformers (p < 0.01)
6. **Prune** - Remove ineffective ads
7. **Optimize** - Calculate average CTR, purchase high-performing slots
8. **Goal** - Minimize ad spend while maximizing conversions

## Manual Ad Generation (Legacy)

### How It Works

### 1. Image Preprocessing
- Base images are resized to a maximum dimension of 970px while maintaining aspect ratio
- Portrait images: scaled by height
- Landscape images: scaled by width
- Square images: kept at original dimensions

### 2. Sliding Window Cropping
- A sliding window moves across the resized image in 50px steps
- For each ad size, all valid crop positions are saved
- Crops that exceed image boundaries are automatically skipped

### 3. Text Overlay Generation
For each crop, the script generates variations with:
- **Text messages**: "Buy Now!", "Limited Time Offer!", "Best Prices Guaranteed!"
- **Font sizes**: 16, 20, 24
- **Positions**: top, middle, bottom
- **Styling**: White text with black outline for maximum readability

### 4. Output Organization
Each crop gets its own folder containing:
- One preview image (no text)
- Subfolders per font size, each containing 9 variations (3 texts × 3 positions)

## Usage

### Basic Usage

1. Place your base images (JPG format) in `base_images/` folder
2. Run the script:
```bash
python main.py
```

### Customization

Edit `main.py` to customize:

**Ad sizes** (line 19-32):
```python
ad_sizes = [
    (300, 250),
    (728, 90),
    # Add or remove sizes as needed
]
```

**Ad text** (line 34-37):
```python
ad_text = [
    "Buy Now!",
    "Your Custom Text!",
]
```

**Font sizes** (line 39):
```python
font_sizes = [16, 20, 24, 32]  # Add more sizes
```

**Cropping parameters** (line 282):
```python
generate_ad_crops(
    base_images_dir,
    output_base_dir,
    max_dimension=970,  # Maximum image dimension
    step_size=50        # Sliding window step size
)
```

## Output Statistics

For a single base image, the script generates approximately:
- **Crops per ad size**: Variable (depends on image dimensions and step size)
- **Variations per crop**: 27 (3 font sizes × 3 texts × 3 positions)
- **Total**: Hundreds to thousands of unique ad variations

Example: A 1920x1080 image might generate:
- 12 ad sizes
- ~10-50 crops per size (average)
- ~27 variations per crop
- **= 3,240 - 16,200 total ad images**

## Logging

The script provides detailed progress information:
- Image processing status (portrait/landscape/square detection)
- Resize dimensions
- Crop counts per ad size
- Progress bars for images, ad sizes, and crop generation

To enable debug logging, change line 14 in `main.py`:
```python
level=logging.DEBUG  # More detailed output
```

## Technical Details

### AI Generation Pipeline

**Model**: Compatible with any Stable Diffusion `.safetensors` model
- Uses `diffusers` library with DPM scheduler
- Generates single 1024x1024 master image
- Smart cropping maintains subject in frame
- Animated GIFs created via sliding window across master

**Panning Logic**:
- Landscape ads (width > height): Pan top-to-bottom
- Portrait/Square ads: Pan left-to-right
- Configurable frame count and duration

### Statistical Approach

Following guidelines in `CLAUDE.md`:
- **Minimum impressions**: 5,000 per ad site
- **P-value threshold**: 0.01 for click significance
- **Test duration**: Minimum 24 hours (covers daily variation)
- **Method**: One-sided binomial test (H1: CTR < target)
- **Goal**: Minimize false positives when pruning

### Competitor Analysis

The ad scraper targets 50+ JuicyAds network sites:
- Identifies ad containers via iframe, ins tags, and common classes
- Waits 10 seconds for async ad loading
- Extracts both image and destination URL
- Browser runs visible (non-headless) for debugging

## Font Support

The script attempts to load Comic Sans MS (for bold, attention-grabbing text), with fallbacks:
- Linux: Liberation Sans, DejaVu Sans
- macOS: System Comic Sans MS
- Windows: Comic Sans from Fonts directory
- Fallback: Arial or system default

## Performance Notes

- Generation time varies based on base image size and quantity
- Uses PIL/Pillow for efficient image processing
- Progress bars track completion (via tqdm)
- JPEG quality set to 95 for high-quality output
- Crops are generated on-the-fly (not stored in memory)

## Troubleshooting

**No images found**: Ensure JPG files are in `base_images/` directory

**Font warnings**: Install TrueType fonts or the script will use system defaults

**Memory issues**: Process images one at a time or reduce `max_dimension`

**Too many files**: Reduce `step_size` or limit `ad_sizes` array

## Future Enhancements

### Planned Features
1. **JuicyAds API** - Build custom API wrapper (no official API exists)
2. **Conversion Tracking** - Track clicks → bids → watchers pipeline
3. **Email List Builder** - Capture interested viewers for repeat marketing
4. **Slot Purchasing** - Auto-detect high-performing zones and calculate bulk pricing
5. **eBay Partner Network** - Research integration for additional revenue streams
6. **Auto-deployment** - Upload generated ads directly to ad networks
7. **Dashboard** - Real-time CTR monitoring and optimization suggestions

### Key Questions to Answer
- Are clicks converting to bids or watchers?
- What's the cost per conversion?
- Would email list building be more profitable than direct ads?
- Which ad sizes/positions perform best per site?
- What time windows have highest CTR?

## Notes

- See `CLAUDE.md` for platform configuration and testing parameters
- Ad scraper currently targets JuicyAds network only
- AI generator requires GPU (CUDA) for reasonable generation times (~2-5 min per batch)
- Manual generator is CPU-friendly but requires pre-existing images
- All statistics assume minimum 5,000 impressions before pruning decisions

## License

This is a private ad optimization platform for adult content marketing.
