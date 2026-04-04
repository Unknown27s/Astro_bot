#!/usr/bin/env python3
"""
Batch Watermark Removal Tool for AstroBot Project
For removing watermarks/logos from multiple project photos

Features:
- Intelligent watermark detection (color-based)
- Content-aware inpainting (uses surrounding pixels)
- Batch processing (10-20+ images)
- Preview masks before processing
- Multiple removal strategies
"""

import cv2
import numpy as np
import os
from pathlib import Path
from typing import Optional, Tuple
import argparse
from datetime import datetime


class WatermarkRemover:
    """Remove watermarks from images using OpenCV inpainting"""

    def __init__(self, method='telea'):
        """
        Initialize remover

        Args:
            method: 'telea' (faster) or 'ns' (slower, slightly better)
        """
        self.method = cv2.INPAINT_TELEA if method == 'telea' else cv2.INPAINT_NS
        self.method_name = method

    def auto_detect_watermark(self, image_path: str) -> Optional[np.ndarray]:
        """
        Automatically detect watermark area by color

        Returns: Binary mask (white=watermark, black=keep)
        """
        img = cv2.imread(image_path)
        if img is None:
            return None

        # Convert to HSV for better color detection
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Detect darker areas (typical watermark color)
        # Customize these ranges based on your watermark color
        lower_bound = np.array([0, 0, 0])
        upper_bound = np.array([180, 255, 100])  # Dark pixels

        mask = cv2.inRange(hsv, lower_bound, upper_bound)

        # Clean up mask: remove noise, connect regions
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        return mask

    def interactive_mask_creation(self, image_path: str) -> Optional[np.ndarray]:
        """
        Create mask by manually drawing on watermark areas

        Controls:
        - Click and drag to mark watermark areas
        - 'S' to save and proceed
        - 'R' to reset
        - 'Q' to quit
        """
        img = cv2.imread(image_path)
        if img is None:
            return None

        display = img.copy()
        mask = np.zeros(img.shape[:2], dtype=np.uint8)
        drawing = False

        def draw_circle(event, x, y, flags, param):
            nonlocal drawing, display
            if event == cv2.EVENT_LBUTTONDOWN:
                drawing = True
            elif event == cv2.EVENT_MOUSEMOVE and drawing:
                cv2.circle(mask, (x, y), 15, 255, -1)
                cv2.circle(display, (x, y), 15, (0, 255, 0), 2)
                cv2.imshow(f'Mark Watermark in {Path(image_path).name}', display)
            elif event == cv2.EVENT_LBUTTONUP:
                drawing = False

        cv2.namedWindow(f'Mark Watermark in {Path(image_path).name}')
        cv2.setMouseCallback(f'Mark Watermark in {Path(image_path).name}', draw_circle)
        cv2.imshow(f'Mark Watermark in {Path(image_path).name}', display)

        print(f"\n🎨 Marking watermark in {Path(image_path).name}")
        print("   Click and drag to mark watermark areas (green circle)")
        print("   'S' = Save & Process  |  'R' = Reset  |  'Q' = Skip this image")

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):
                cv2.destroyAllWindows()
                return mask if np.any(mask) else None
            elif key == ord('r'):
                mask = np.zeros(img.shape[:2], dtype=np.uint8)
                display = img.copy()
                cv2.imshow(f'Mark Watermark in {Path(image_path).name}', display)
            elif key == ord('q'):
                cv2.destroyAllWindows()
                return None

    def remove_watermark(self, image_path: str, output_path: str,
                        mask: Optional[np.ndarray] = None,
                        radius: int = 3) -> bool:
        """
        Remove watermark using inpainting

        Args:
            image_path: Input image
            output_path: Output image
            mask: Binary mask (None = auto-detect)
            radius: Inpainting neighborhood radius

        Returns: True if successful
        """
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ Could not load: {image_path}")
            return False

        # Auto-detect if no mask provided
        if mask is None:
            mask = self.auto_detect_watermark(image_path)
            if mask is None or not np.any(mask):
                print(f"⚠️  No watermark detected in {Path(image_path).name}, skipping")
                return False

        # Apply inpainting
        try:
            result = cv2.inpaint(img, mask, radius, self.method)
            cv2.imwrite(output_path, result)
            print(f"✅ Removed watermark: {Path(image_path).name} → {Path(output_path).name}")
            return True
        except Exception as e:
            print(f"❌ Error processing {image_path}: {e}")
            return False

    def preview_mask(self, image_path: str, mask: Optional[np.ndarray] = None):
        """Show mask visualization before processing"""
        img = cv2.imread(image_path)
        if img is None:
            return

        if mask is None:
            mask = self.auto_detect_watermark(image_path)

        # Create visualization
        h, w = img.shape[:2]
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) if len(mask.shape) == 2 else mask

        # Show mask areas in red on original
        result = img.copy()
        result[mask > 100] = [0, 0, 255]  # Red for watermark areas

        combined = np.hstack([img, result, np.stack([mask]*3, axis=2)])

        cv2.imshow(f"Preview: {Path(image_path).name}", combined)
        print("Press any key to close preview")
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def batch_remove_watermarks(input_dir: str, output_dir: str,
                           interactive: bool = False,
                           preview: bool = False,
                           extensions: tuple = ('.jpg', '.jpeg', '.png', '.bmp')):
    """
    Batch remove watermarks from all images in directory

    Args:
        input_dir: Directory with watermarked images
        output_dir: Directory to save cleaned images
        interactive: Manually mark each watermark
        preview: Show mask preview before processing
        extensions: Image file extensions to process
    """

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all images
    images = []
    for ext in extensions:
        images.extend(input_path.glob(f'*{ext}'))
        images.extend(input_path.glob(f'*{ext.upper()}'))

    if not images:
        print(f"❌ No images found in {input_dir}")
        return

    print(f"\n{'='*60}")
    print(f"🖼️  Found {len(images)} image(s) to process")
    print(f"{'='*60}\n")

    remover = WatermarkRemover()
    processed = 0
    skipped = 0

    for i, img_path in enumerate(images, 1):
        print(f"\n[{i}/{len(images)}] Processing: {img_path.name}")

        mask = None
        if interactive:
            mask = remover.interactive_mask_creation(str(img_path))
            if mask is None:
                print(f"⏭️  Skipped (user)")
                skipped += 1
                continue
        elif preview:
            remover.preview_mask(str(img_path))

        # Process image
        output_file = output_path / img_path.name
        if remover.remove_watermark(str(img_path), str(output_file), mask):
            processed += 1
        else:
            skipped += 1

    print(f"\n{'='*60}")
    print(f"📊 Summary: {processed} processed, {skipped} skipped")
    print(f"✅ Cleaned images saved to: {output_dir}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Batch remove watermarks from project photos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto-detect watermarks in all images
  python watermark_remover.py --input ./photos --output ./cleaned_photos

  # Preview masks before processing
  python watermark_remover.py --input ./photos --output ./cleaned_photos --preview

  # Manually mark each watermark
  python watermark_remover.py --input ./photos --output ./cleaned_photos --interactive
        """
    )

    parser.add_argument('--input', '-i', required=True,
                       help='Input directory with watermarked images')
    parser.add_argument('--output', '-o', required=True,
                       help='Output directory for cleaned images')
    parser.add_argument('--interactive', action='store_true',
                       help='Manually mark watermark areas for each image')
    parser.add_argument('--preview', action='store_true',
                       help='Show mask preview before processing')
    parser.add_argument('--method', choices=['telea', 'ns'], default='telea',
                       help='Inpainting method (telea=faster, ns=better)')

    args = parser.parse_args()

    batch_remove_watermarks(
        input_dir=args.input,
        output_dir=args.output,
        interactive=args.interactive,
        preview=args.preview
    )


if __name__ == '__main__':
    main()
