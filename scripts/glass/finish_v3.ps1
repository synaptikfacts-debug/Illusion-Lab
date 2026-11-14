$d = 'C:\IllusionLab\out\0015-glass'
$p = 'C:\IllusionLab\publish\0015-liquid-glass-v3'
while ((Get-ChildItem "$d\final3\*.png").Count -lt 1320) { Start-Sleep 10 }
Start-Sleep 5
New-Item -ItemType Directory -Force $p, "$p\thumbnails", "$d\check3" | Out-Null
# YouTube master: high bitrate
ffmpeg -y -loglevel error -framerate 60 -i "$d\final3\f%05d.png" -i "$d\audio.wav" -map 0:v -map 1:a -c:v libx264 -preset slow -crf 14 -profile:v high -level 4.2 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -g 30 -c:a aac -b:a 320k -ar 48000 -shortest -movflags +faststart "$p\YOUTUBE_0015-liquid-glass_master.mp4"
# TikTok / Instagram / Facebook / X: lighter, well under limits
ffmpeg -y -loglevel error -framerate 60 -i "$d\final3\f%05d.png" -i "$d\audio.wav" -map 0:v -map 1:a -c:v libx264 -preset slow -crf 19 -maxrate 14M -bufsize 28M -profile:v high -level 4.2 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -g 60 -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$p\SOCIAL_0015-liquid-glass_tiktok-ig-fb-x.mp4"
# checks: contact frames (opening, signature freeze, ending + loop pair)
foreach ($f in 0, 30, 60, 120, 1005, 1050, 1140, 1200, 1290, 1319) { Copy-Item ("$d\final3\f{0:D5}.png" -f $f) "$d\check3\" }
# covers: most striking frame = finale freeze (t = 17.5 s, frame 1050)
Copy-Item "$d\final3\f01050.png" "$p\cover_source.png"
'FINISHED' | Out-File "$d\finish3.done"

