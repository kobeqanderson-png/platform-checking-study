# Tracks every recording for one day, in time order. Usage: run_day.ps1 <day, e.g. d1>
param([string]$Day)
$d = "C:\Users\kobeq\Videos\check_audit\tracking_pilot"; $py = (Get-Command python).Source
$out = "$d\tracks_$Day"; New-Item -ItemType Directory -Force $out | Out-Null
$i = 0
Get-ChildItem "C:\Users\kobeq\OneDrive\Pictures\Camera Roll\$Day videos" -Filter *.mp4 | Sort-Object Name | ForEach-Object {
  $i++
  "file$i = $($_.Name)"
  & $py -I "$d\track_recording.py" $_.FullName "$out\file${i}_$($_.BaseName -replace '[^0-9A-Za-z_-]','_').csv" 2>&1
}
