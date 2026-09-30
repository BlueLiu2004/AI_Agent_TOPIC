$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$videoRoot = Split-Path -Parent $PSScriptRoot
$cues = Get-Content -LiteralPath (Join-Path $videoRoot 'src/data/cues.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$audioDir = Join-Path $videoRoot 'public/audio/raw'
New-Item -ItemType Directory -Force -Path $audioDir | Out-Null
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SelectVoice('Microsoft Hanhan Desktop')
$synth.Rate = 0
$synth.Volume = 100
try {
  for ($i = 0; $i -lt $cues.Count; $i++) {
    $phrase = $cues[$i].text
    if ($cues[$i].speech) { $phrase = $cues[$i].speech }
    $file = Join-Path $audioDir ('cue-{0:d2}.wav' -f $i)
    $synth.SetOutputToWaveFile($file)
    $synth.Speak($phrase)
    $synth.SetOutputToNull()
  }
} finally { $synth.Dispose() }
Write-Output ('Generated {0} local zh-TW voice clips.' -f $cues.Count)
