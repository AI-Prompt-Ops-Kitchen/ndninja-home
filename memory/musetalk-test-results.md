# MuseTalk Test Results - 2026-01-27

## Summary
**Pipeline Status**: ✅ Working on Vengeance (RTX 4090, Docker + WSL2)
**Ninja Avatar**: ⚠️ Partially working — video generated but with caveats

## Test Results

### Test 1: Sample Face (yongen.mp4) + Ninja Audio ✅
- **Status**: SUCCESS
- **Output**: `media/yongen_ninja_test.mp4` (1.7MB, 8.8s, 25fps)
- **Details**: Normal human face lip-synced to ninja_test.wav audio perfectly
- **Pipeline confirmed working end-to-end**

### Test 2: Ninja Avatar (ninja_avatar.jpg) + Ninja Audio ⚠️
- **Status**: PARTIAL SUCCESS — video generated with face detection workaround
- **Output**: `media/ninja_test_output.mp4` (614KB, 8.8s, 289x512, 25fps)
- **Details**: Required patching preprocessing.py to work

## Issues Encountered & Fixes

### Issue 1: s3fd Face Detection Failure (CRITICAL)
- **Problem**: The ninja avatar has a black mask covering the entire lower face (nose, mouth, chin). The s3fd face detector returns `None` — it cannot detect a face.
- **Error**: `division by zero` in `get_landmark_and_bbox()` when computing average_range_minus/plus from empty lists
- **Fix Applied**: Patched `preprocessing.py` to use dwpose body pose landmarks (keypoints 23-91) as fallback bounding box when s3fd fails
- **Fallback bbox detected**: `(63, 60, 198, 216)` from dwpose landmarks
- **File**: `musetalk/utils/preprocessing.py` (backup at `.bak`)

### Issue 2: No libx264 in Docker ffmpeg
- **Problem**: Docker image uses conda ffmpeg 4.3 which only has libopenh264, not libx264. The `-crf 18` option is unrecognized.
- **Error**: `Unknown encoder 'libx264'` and `Unrecognized option 'crf'`
- **Fix Applied**: Changed inference.py to use `mpeg4 -q:v 5` instead of `libx264 -crf 18`
- **File**: `scripts/inference.py`

### Issue 3: NumPy Array Compatibility Warnings
- **Problem**: During frame compositing (padding generated faces back to original size), RuntimeError about "C subclassed NumPy array" appears repeatedly
- **Impact**: Non-fatal — frames still generated and video assembled successfully
- **Root Cause**: NumPy version mismatch between the library that produces arrays and the one consuming them (likely mmpose vs opencv)
- **Status**: Not fixed, but doesn't block output

### Issue 4: v15 Hardcodes bbox_shift=0
- **Discovery**: In inference.py line 94: `bbox_shift = 0  # v15 uses fixed bbox_shift`
- **Impact**: The `bbox_shift` config parameter is IGNORED for v15. Only v1 respects it.
- **Workaround**: Would need to use `--version v1` (different model) or patch inference.py

### Issue 5: `save_dir_full` Not Set for Image Input
- **Problem**: When input is a single image (not video), `save_dir_full` is never assigned, but cleanup code tries `shutil.rmtree(save_dir_full)`
- **Impact**: Non-fatal error at cleanup, doesn't affect video output
- **Status**: Known bug in MuseTalk, not fixed

## Key Findings About Ninja Avatar + MuseTalk

### The Core Challenge
MuseTalk is designed for **human faces with visible mouths**. It:
1. Detects a face using s3fd (S³FD face detector)
2. Extracts face landmarks using DWPose (body keypoints 23-91 = face region)
3. Crops the lower face region
4. Generates lip-sync frames using a UNet conditioned on Whisper audio features
5. Composites the generated lower face back onto the original frame

For the ninja avatar:
- **s3fd completely fails** — the mask prevents face detection
- **DWPose still detects body/face keypoints** — even through the mask, it finds approximate face landmark positions
- The generated frames try to synthesize a mouth **through/on top of the mask**

### What the Output Looks Like
The ninja video was generated at 289x512, 8.8 seconds. The face parsing and compositing step runs but produces numpy warnings. The model attempts to generate lip movements in the masked region. Quality assessment needed (user should review).

### Recommendations for Better Results
1. **Use an unmasked version of the ninja face** — render the avatar without the mask for the lip-sync source, then composite the mask back with transparency
2. **Use a hybrid approach**: Generate lip-sync with a human face placeholder, then transfer just the mouth movements to the avatar using a separate compositing step
3. **Try SadTalker or similar** — some tools handle stylized/cartoon faces better
4. **Custom training data** — MuseTalk could potentially be fine-tuned on masked face data
5. **Consider Wav2Lip** — simpler model that might be more adaptable to masked faces

## Files Modified on Vengeance
- `/home/steam/musetalk/musetalk/utils/preprocessing.py` — Patched for fallback bbox (backup at `.bak`)
- `/home/steam/musetalk/scripts/inference.py` — Patched mpeg4 codec
- `/home/steam/musetalk/configs/inference/sample_test.yaml` — Test config for yongen
- `/home/steam/musetalk/configs/inference/ninja_bbox_test.yaml` — Test config for bbox shift

## Output Files
- `media/ninja_test_output.mp4` — Ninja avatar lip-sync (main test)
- `media/yongen_ninja_test.mp4` — Sample face lip-sync (pipeline validation)
- `media/ninja_avatar.jpg` — The ninja avatar source image

## Docker Setup Reference
```bash
# Run MuseTalk inference
docker run --rm --gpus all -v /home/steam/musetalk:/app musetalk python -m scripts.inference \
  --inference_config ./configs/inference/ninja_test.yaml \
  --result_dir ./results/ninja_test \
  --unet_model_path ./models/musetalkV15/unet.pth \
  --unet_config ./models/musetalkV15/musetalk.json \
  --version v15
```
