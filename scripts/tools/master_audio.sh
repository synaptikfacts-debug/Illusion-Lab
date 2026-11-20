#!/bin/bash
# usage: master_audio.sh <in.wav> <out.wav>  -> phone-forward EQ + gentle compression, -14 LUFS, -1.5 dBFS peak
IN=$1; OUT=$2; TMP=${OUT%.wav}_eq.wav
ffmpeg -v error -y -i "$IN" -af "equalizer=f=380:t=q:w=0.8:g=8,equalizer=f=850:t=q:w=1:g=6,lowshelf=f=90:g=-6,acompressor=threshold=0.1:ratio=3:attack=4:release=150:knee=4" "$TMP"
g=6
for i in 1 2 3 4 5; do
  ffmpeg -v error -y -i "$TMP" -af "volume=${g}dB,alimiter=limit=0.84:attack=3:release=80:level=disabled" -ar 48000 "$OUT"
  I=$(ffmpeg -hide_banner -i "$OUT" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
  d=$(node -e "console.log((-14-($I)).toFixed(2))")
  node -e "process.exit(Math.abs($d)<0.25?0:1)" && break
  g=$(node -e "console.log(($g+$d*1.15).toFixed(2))")
done
echo "full: $(ffmpeg -hide_banner -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I:|Peak:)' | tr -s ' ' | tr '\n' ' ')"
echo "phone: $(ffmpeg -hide_banner -i "$OUT" -af highpass=f=200,highpass=f=200,ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I:|Peak:)' | tr -s ' ' | tr '\n' ' ')"
