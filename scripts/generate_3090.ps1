# Launch Wan2.2 TI2V-5B with the settings that are known to work on a
# 24GB RTX 3090 / 48GB RAM Windows machine (see docs/WINDOWS_RTX3090.md).
#
# Usage:
#   .\scripts\generate_3090.ps1 -Prompt "your prompt" -Out video.mp4
#   .\scripts\generate_3090.ps1 -Prompt "..." -Steps 30 -Frames 49 -DryRun
param(
    [Parameter(Mandatory = $true)][string]$Prompt,
    [string]$Out = "out.mp4",
    [int]$Steps = 50,
    [int]$Frames = 121,
    [string]$Size = "1280*704",
    [int]$VaeTile = 16,
    [string]$CkptDir = ".\Wan2.2-TI2V-5B",
    [switch]$DryRun
)

$env:PYTORCH_CUDA_ALLOC_CONF = "expandable_segments:True"
$env:PYTHONIOENCODING = "utf-8"

$cmd = @(
    "generate.py",
    "--task", "ti2v-5B",
    "--size", $Size,
    "--ckpt_dir", $CkptDir,
    "--offload_model", "True",
    "--convert_model_dtype",
    "--t5_cpu",
    "--vae_tile", $VaeTile,
    "--frame_num", $Frames,
    "--sample_steps", $Steps,
    "--save_file", $Out,
    "--prompt", $Prompt
)

if ($DryRun) {
    "python " + (($cmd | ForEach-Object { if ($_ -match '\s|\*') { '"' + $_ + '"' } else { $_ } }) -join " ")
    return
}
python @cmd
