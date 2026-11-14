$d = 'C:\IllusionLab\out\0016-bloom'
$p = 'C:\IllusionLab\publish\0016-midnight-bloom'
while ((Get-ChildItem "$d\final\*.png").Count -lt 1020) { Start-Sleep 10 }
Start-Sleep 5
New-Item -ItemType Directory -Force $p, "$p\thumbnails" | Out-Null
$vf = "fade=t=out:st=16.0:d=1.0"
ffmpeg -y -loglevel error -framerate 60 -i "$d\final\f%05d.png" -i "$d\audio.wav" -map 0:v -map 1:a -vf $vf -c:v libx264 -preset slow -crf 14 -profile:v high -level 4.2 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -g 30 -c:a aac -b:a 320k -ar 48000 -af "alimiter=limit=0.80:level=false" -shortest -movflags +faststart "$p\YOUTUBE_0016-midnight-bloom_master.mp4"
ffmpeg -y -loglevel error -framerate 60 -i "$d\final\f%05d.png" -i "$d\audio.wav" -map 0:v -map 1:a -vf $vf -c:v libx264 -preset slow -crf 19 -maxrate 14M -bufsize 28M -profile:v high -level 4.2 -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 -g 60 -c:a aac -b:a 192k -ar 48000 -af "alimiter=limit=0.74:level=false" -shortest -movflags +faststart "$p\SOCIAL_0016-midnight-bloom_tiktok-ig-fb-x.mp4"
Copy-Item "$d\final\f00210.png" "$p\cover_source_hero.png"
Copy-Item "$d\final\f00480.png" "$p\cover_source_wave.png"
'FINISHED' | Out-File "$d\finish.done"
