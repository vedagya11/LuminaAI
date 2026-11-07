# Model weights

`zerodce_pp_epoch99.pth` is the Epoch99 Zero-DCE++ checkpoint published by Chongyi Li, Chunle Guo, and Chen Change Loy.

- Source: https://github.com/Li-Chongyi/Zero-DCE_extension/blob/main/Zero-DCE++/snapshots_Zero_DCE++/Epoch99.pth
- SHA-256: `ca8855b90df9a80fa4195a831f33d3476b1964f787eb70602797c773067f3b84`
- Paper: Li, Guo, Loy. Learning to Enhance Low-Light Image via Zero-Reference Deep Curve Estimation. IEEE TPAMI, 2022.
- License: the upstream repository does not include a LICENSE file. LUMINA AI does not relicense the checkpoint. Keep the attribution above if you redistribute it.

The loader refuses this filename when the hash does not match. A different checkpoint can be supplied with `ZERODCE_WEIGHTS=/path/to/checkpoint.pth` if it matches the Zero-DCE++ `enhance_net_nopool` state dict. A missing or unreadable file makes Deep Learning and Hybrid AI unavailable. Classical CV keeps working.

Inference runs on CPU. Images whose long side exceeds `MAX_INFERENCE_SIDE` (default 1280) are reduced for the forward pass and the result is resized back. The API reports that resize in `model.resized_for_inference`.
