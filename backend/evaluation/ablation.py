"""Classical ablation on one synthetic dark frame.

Prints measured luminance only. It does not stand in for a dataset result.

    python -m evaluation.ablation
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.enhance import enhance_classical


def main() -> int:
    image = np.full((128, 160, 3), 24, dtype=np.uint8)
    image[40:90, 30:80] = (12, 16, 48)
    variants = {
        "full": {},
        "without_denoise": {"use_denoise": False},
        "without_white_balance": {"use_gray_world": False},
        "without_retinex": {"use_retinex": False},
        "without_clahe": {"use_clahe": False},
        "without_unsharp": {"use_unsharp": False},
        "without_highlight_rolloff": {"use_highlight_rolloff": False},
        "without_chroma_restore": {"use_chroma_restore": False},
    }
    print("Synthetic dark frame. Mean output luminance and stages:")
    for name, flags in variants.items():
        _restored, meta = enhance_classical(image, **flags)
        print(
            f"  {name}: luminance {meta['input']['mean_luminance']} -> "
            f"{meta['output']['mean_luminance']} gamma={meta['gamma']} stages={','.join(meta['stages'])}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
