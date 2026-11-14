$d = 'C:\IllusionLab\out\0015-glass'
$p = 'C:\IllusionLab\publish\0015-liquid-glass-final'
while ((Get-ChildItem "$d\final3\*.png").Count -lt 1470) { Start-Sleep 10 }
Start-Sleep 5
New-Item -ItemType Directory -Force $p, "$p\thumbnails", "$d\checkE" | Out-Null
$vf = "fade=t=out:st=23.6:d=0.9"
ffmpeg -y -loglevel error -framerate 60 -i "$d\final3\f%05d.png" -i "$d\audio_end.wav" -map 0:v -map 1:a -vf $vf -c:v libx264 -preset slow -crf 14 -profile:v high -level 4.2 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -g 30 -c:a aac -b:a 320k -ar 48000 -af "alimiter=limit=0.80:level=false" -shortest -movflags +faststart "$p\YOUTUBE_0015-liquid-glass_master.mp4"
ffmpeg -y -loglevel error -framerate 60 -i "$d\final3\f%05d.png" -i "$d\audio_end.wav" -map 0:v -map 1:a -vf $vf -c:v libx264 -preset slow -crf 19 -maxrate 14M -bufsize 28M -profile:v high -level 4.2 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -g 60 -c:a aac -b:a 192k -ar 48000 -af "alimiter=limit=0.74:level=false" -shortest -movflags +faststart "$p\SOCIAL_0015-liquid-glass_tiktok-ig-fb-x.mp4"
Copy-Item "C:\IllusionLab\publish\0015-liquid-glass-v3\thumbnails\*" "$p\thumbnails\" -Force
foreach ($f in 0, 1188, 1230, 1280, 1300, 1330, 1360, 1400, 1440, 1469) { Copy-Item ("$d\final3\f{0:D5}.png" -f $f) "$d\checkE\" }
'FINISHED' | Out-File "$d\finishE.done"
