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

## Thermals

At full load the card hit 88.6C core / 105.5C hot spot / 82C memory junction.
An undervolt (1740 MHz locked at ~870mV, power limit 85%) cut power from 347W
to 315W with the same speed (25.0 s/step) but only lowered the hot spot to
103.7C. If the hot spot stays above ~100C, clean the heatsink and repaste the
core; the memory pads were fine.

## Ideas not done yet

- TeaCache or cache-dit for fewer effective steps (needs quality validation).
- A 4-step community TI2V-5B distillation (no official lightx2v LoRA exists
  for the 5B model).
- SageAttention: reported to produce noise on the 5B model.
