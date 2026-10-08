# Wan2.2 TI2V-5B on Windows with an RTX 3090 (24GB) and 48GB RAM

Measured on an i7-13700K, RTX 3090, 48GB RAM, Windows 11, torch 2.6.0+cu124.

## Quick start

    .\scripts\generate_3090.ps1 -Prompt "your prompt" -Out video.mp4

This runs `generate.py --task ti2v-5B --size 1280*704 --offload_model True
--convert_model_dtype --t5_cpu --vae_tile 16` (5 s, 121 frames, 50 steps).

## Windows requirements

- **Pagefile.** Windows crashed with an access violation (exit 139) whenever
  committed memory (RAM + pagefile) ran out. Use a fixed pagefile of at least
  32-40GB on a fast NVMe drive (initial size = maximum, so it does not grow
  during allocation). Commit limit was ~80GB with 48GB RAM.
- **safetensors 0.4.5.** safetensors 0.8.0 crashed in `load_file`.
- **No flash_attn needed.** `wan/modules/model.py` calls `attention()`, which
  falls back to PyTorch SDPA when flash_attn is not installed.

## Memory and speed changes in this fork

- T5 is built directly in bf16, the DiT is loaded in its final dtype, and the
  T5 encoder is dropped from RAM once the prompts are encoded. Peak committed
  memory with 2 steps: 76.1GB -> 66.1GB.
- `--vae_tile 16` (ported from upstream PR #393) decodes in overlapping
  spatial tiles. 121 frames: decode+save ~7.8 min -> ~4.7 min, committed
  memory 66.1GB -> 56.7GB. On the same latent the result differs from the
  full-frame decode by 58 dB PSNR. Tile 16 / overlap 4 was fastest; tile 24
  was slower.

## Reference timings (1280x704, 121 frames, 50 steps)

Load ~4 min, diffusion 21 min (25.2 s/step), decode+save 8 min without
`--vae_tile`. Peak VRAM 24.2GB, so nothing else should use the GPU.

## 30 vs 50 steps (same prompt and seed, 121 frames, `--vae_tile 16`)

30 steps: 21 min total (diffusion 12.5 min). 50 steps (no tiling): ~33 min.
Both videos are coherent, but in sampled frames the 30-step one had more
anatomy artifacts (a white blob where a cat's head should be, boot-like feet);
the 50-step one was cleaner. One sample each, so not conclusive. Use 30 for
drafts and 50 for finals.

## Thermals

At full load the card hit 88.6C core / 105.5C hot spot / 82C memory junction.
An undervolt (1740 MHz locked at ~870mV, power limit 85%) cut power from 347W
to 315W with the same speed (25.0 s/step) but only lowered the hot spot to
103.7C. If the hot spot stays above ~100C, clean the heatsink and repaste the
core; the memory pads were fine.

## TeaCache (`--teacache_thresh`, off by default)

Skips the DiT blocks on steps whose first-block modulated input barely
changed and re-applies the cached residual (kept on the CPU, VRAM is full).
Uncalibrated for the 5B model, so the threshold is on the raw relative L1:
per-step changes are ~0.02-0.13. 30 steps, same prompt and seed, `--vae_tile 16`:

| threshold | steps run | diffusion | total | quality |
|---|---|---|---|---|
| off | 30/30 | 12.5 min | 21.2 min | baseline |
| 0.04 | 22/30 | 9.5 min | 18.6 min | clean in sampled frames |
| 0.15 | 10/30 | 4.5 min | 13.6 min | unusable (blurry, smeared) |

0.04 gives ~1.3x on diffusion (-12% total, since load and decode are fixed).
Do not go to 0.15. One sample per setting; judged by eye.

## Ideas not done yet

- cache-dit.
- A 4-step community TI2V-5B distillation (no official lightx2v LoRA exists
  for the 5B model).
- SageAttention: reported to produce noise on the 5B model.
