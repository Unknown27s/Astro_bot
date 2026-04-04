# Watermark Removal Tool

Batch removal of watermarks from project photos using content-aware inpainting.

## Quick Start

### 1. Install OpenCV (if not already installed)
```bash
pip install opencv-python numpy
```

### 2. Auto-Detect & Remove Watermarks

```bash
python tools/watermark_remover.py --input ./photos --output ./cleaned_photos
```

This automatically detects watermark areas and removes them.

### 3. Preview Masks First (Recommended)

```bash
python tools/watermark_remover.py --input ./photos --output ./cleaned_photos --preview
```

Shows expected watermark detection before processing.

### 4. Manually Mark Watermarks

For precise control, mark each watermark by hand:

```bash
python tools/watermark_remover.py --input ./photos --output ./cleaned_photos --interactive
```

**Controls in interactive mode:**
- **Click & Drag** = Mark watermark area (green circle)
- **S** = Save & Process
- **R** = Reset mask
- **Q** = Skip image

## Usage Examples

### Basic (Auto-detect all)
```bash
python tools/watermark_remover.py -i photos -o cleaned
```

### Preview before processing
```bash
python tools/watermark_remover.py -i photos -o cleaned --preview
```

### Manual marking (best for complex marks)
```bash
python tools/watermark_remover.py -i photos -o cleaned --interactive
```

### Change inpainting method (better quality)
```bash
python tools/watermark_remover.py -i photos -o cleaned --method ns
```

## Methods

| Method | Speed | Quality | When to Use |
|--------|-------|---------|------------|
| `telea` | Fast | Good | Quick batch processing |
| `ns` (Navier-Stokes) | Slower | Better | For difficult watermarks |

## Troubleshooting

### "No watermark detected"
The auto-detection threshold may need adjustment. Try:
1. Preview mode to see what's being detected
2. Manual marking for more control

### Poor quality results
- Try `--method ns` for better inpainting
- Manually mark watermarks instead of auto-detect
- Experiment with watermark color thresholds in the code

### Image not loading
- Ensure image format is supported (JPG, PNG, BMP, etc.)
- Check file path and permissions

## Advanced: Customizing Watermark Detection

Edit `watermark_remover.py` and modify these lines in `auto_detect_watermark()`:

```python
# Current: detects dark areas
lower_bound = np.array([0, 0, 0])
upper_bound = np.array([180, 255, 100])
```

**Example: Detect white watermarks:**
```python
lower_bound = np.array([0, 0, 150])
upper_bound = np.array([180, 50, 255])
```

**Example: Detect specific color (e.g., yellow logo):**
```python
# Yellow range in HSV
lower_bound = np.array([20, 100, 100])
upper_bound = np.array([30, 255, 255])
```

## Output

- ✅ Cleaned images saved to output directory
- 📊 Summary showing processed/skipped count
- Original images remain untouched

## Requirements

- Python 3.7+
- OpenCV 4.0+
- NumPy

## Notes

- First image may take a moment as OpenCV initializes
- Best results on solid-color watermarks
- Complex watermarks benefit from manual marking
- Inpainting quality depends on surrounding pixel context
