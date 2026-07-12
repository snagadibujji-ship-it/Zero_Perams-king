# AXIMA HELIX — Colab Training Guide

> **For Gemini in Google Colab:** Follow these steps exactly. No modifications needed.
> This trains atom codebooks + 4K upscaler for AXIMA's offline image generation.

---

## WHAT THIS DOES

Trains two things on free Colab GPU:
1. **Atom Codebook** (500K texture tiles from real images) → 40MB
2. **4K Upscaler** (tiny CNN that upscales 256p → 4K) → 10MB

After training, export both files. AXIMA uses them on phone to generate 4K images offline.

---

## STEP 1: Setup Colab

```
1. Go to: https://colab.research.google.com
2. New Notebook
3. Runtime → Change runtime type → GPU (T4 free)
4. Mount Google Drive: (run this cell first)
```

```python
from google.colab import drive
drive.mount('/content/drive')
```

---

## STEP 2: Install Dependencies

```python
!pip install -q torch torchvision datasets scikit-learn onnx
```

---

## STEP 3: Run Training Script

Copy the ENTIRE contents of `scripts/colab_vision_train.py` into a cell and run it.

Or if the repo is accessible:
```python
!git clone https://github.com/snagadibujji-ship-it/industrial-ops-corpus.git /content/repo
!python /content/repo/scripts/colab_vision_train.py
```

---

## STEP 4: Wait (~3-4 hours)

The script will:
- Phase 1: Download training images (10-20 min)
- Phase 2: Extract texture tiles (30-60 min)
- Phase 3: K-means clustering for atoms (60-90 min)
- Phase 4: Train upscaler (60-90 min)
- Phase 5: Export ONNX (1 min)
- Phase 6: Push to GitHub + Google Drive

**Do NOT interrupt.** Progress prints every 10 epochs.

---

## STEP 5: Verify Output

After completion, check:
```python
import os
output_dir = "/content/axima_helix"
for f in os.listdir(output_dir):
    size = os.path.getsize(os.path.join(output_dir, f))
    print(f"  {f}: {size/1024/1024:.1f} MB")
```

Expected output:
```
  atoms_16.bin: ~5-15 MB
  atoms_32.bin: ~15-25 MB
  atoms_64.bin: ~15-25 MB
  upscaler_4k.pth: ~10 MB
  upscaler_4k.onnx: ~10 MB
  training_report.md: <1 MB
```

Total should be ~50-80 MB.

---

## STEP 6: Download to Phone

**Option A — GitHub (if push worked):**
```bash
cd /root/hybrid-ai
git pull
# Files will be in src/data/
```

**Option B — Google Drive:**
```
1. Open Google Drive on phone
2. Go to: My Drive → axima_helix/
3. Download all .bin and .pth files
4. Move to: /root/hybrid-ai/src/data/
```

**Option C — Direct download from Colab:**
```python
from google.colab import files
files.download('/content/axima_helix/atoms_16.bin')
files.download('/content/axima_helix/atoms_32.bin')
files.download('/content/axima_helix/atoms_64.bin')
files.download('/content/axima_helix/upscaler_4k.pth')
```

---

## STEP 7: Verify on Phone

```bash
cd /root/hybrid-ai
python3 -c "
import struct, os
for f in ['src/data/atoms_16.bin', 'src/data/atoms_32.bin', 'src/data/atoms_64.bin']:
    if os.path.exists(f):
        with open(f, 'rb') as fp:
            count = struct.unpack('<I', fp.read(4))[0]
            tile_size = struct.unpack('<H', fp.read(2))[0]
        print(f'  ✓ {f}: {count} atoms @ {tile_size}×{tile_size}')
    else:
        print(f'  ✗ {f}: MISSING')
"
```

---

## WHAT HAPPENS AFTER

Once files are on phone, AXIMA can:
```
"Generate an image of a sunset over ocean"
  → Scene parser extracts: sky(sunset), ocean, horizon
  → Raymarcher renders 256×144 base image (0.5s)
  → Atoms provide real textures (sunset colors, water ripples)
  → Upscaler: 256p → 1024p → 4096p (2s)
  → Output: 4K PNG, physically correct, 3 seconds total
```

---

## TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| "CUDA out of memory" | Reduce BATCH_SIZE to 32 or IMAGE_COUNT to 50000 |
| "Dataset not found" | Script auto-falls back to CIFAR-100 + STL-10 |
| Push to GitHub fails | Download manually via Google Drive or files.download() |
| Training loss not decreasing | Normal for first 10 epochs, patience |
| Colab disconnects | Re-run — script resumes if atoms already saved |
| "No GPU" | Runtime → Change runtime → GPU. If unavailable, wait or use CPU (slower) |

---

## IMPORTANT NOTES

- **Do NOT modify the script** unless you know what you're doing
- Training uses only **public domain / licensed images** (ImageNet, CIFAR, STL)
- The upscaler is **tiny** (2.5M params) — designed to run on CPU in 2 seconds
- Atoms are **real textures from real photos** — that's why images look realistic
- Total output ~50MB fits on ANY phone made after 2015
- After this one-time training, image generation is **free forever offline**

---

## TECHNICAL DETAILS (for Gemini's understanding)

**Atom Codebook:**
- K-means clustering on millions of image tiles
- Each atom = centroid of a cluster = "average texture" for that category
- 16×16 atoms = large-scale color/shape | 32×32 = medium detail | 64×64 = fine texture
- Format: [count:u32][tile_size:u16][channels:u8][float16 pixel data]

**Upscaler:**
- ESPCN architecture (Efficient Sub-Pixel Convolutional Neural Network)
- 5 layers: Conv5×5 → ReLU → Conv3×3 → ReLU → Conv3×3 → ReLU → Conv3×3 → PixelShuffle(4×)
- Input: any resolution RGB | Output: 4× larger in each dimension
- Apply twice: 256p → 1024p → 4096p = 16× total magnification
- Trained with L1 loss (sharper than L2/MSE)

**Why this approach:**
- GPT Image 2 uses billions of params + cloud GPU = $0.41/image
- We use 500K atoms + 2.5M param upscaler = $0/image, offline, phone CPU
- Trade-off: less "creative" but physically correct + deterministic

---

*Owner: Ghias / Gowtham Sangadi*
*Project: AXIMA HELIX (Hybrid-AI vision system)*
