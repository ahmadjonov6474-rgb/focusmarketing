#!/usr/bin/env bash
# Ovozni referens standartiga keltiradi: -14 LUFS, TP -1.2 dB, tor dinamika.
# Ixtiyoriy: fon musiqasi — nutq ostida avtomatik pasayadi (ducking).
#
# Ishlatish:
#   master.sh kirish.mp4 chiqish.mp4 [musiqa.mp3]
set -euo pipefail

IN="${1:?kirish fayl kerak}"
OUT="${2:?chiqish fayl kerak}"
MUSIC="${3:-}"

# Nutq zanjiri: gul-gul tozalash -> siqish -> yumshoq ravnaq
# afade — boshi so'z o'rtasidan boshlansa (yozuv kech yoqilgan bo'lsa)
# qisqa kirish silliqlashtiradi, aks holda "chirt" etib boshlanadi.
FADE="${FADE:-0.05}"
VOICE="highpass=f=85,afftdn=nr=10:nf=-32,acompressor=threshold=-20dB:ratio=4:attack=5:release=140:makeup=2,deesser=i=0.4,afade=t=in:st=0:d=${FADE}"

if [[ -n "$MUSIC" ]]; then
  echo "Musiqa bilan: $MUSIC"
  ffmpeg -y -hide_banner -loglevel warning -stats \
    -i "$IN" -stream_loop -1 -i "$MUSIC" \
    -filter_complex "\
[0:a]${VOICE}[v];\
[v]asplit=2[v1][vsc];\
[1:a]volume=-19dB[m];\
[m][vsc]sidechaincompress=threshold=0.05:ratio=8:attack=12:release=320[mduck];\
[v1][mduck]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix];\
[mix]loudnorm=I=-14:TP=-1.2:LRA=2,alimiter=limit=0.87:level=disabled[aout]" \
    -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -ar 48000 "$OUT"
else
  echo "Musiqasiz"
  ffmpeg -y -hide_banner -loglevel warning -stats \
    -i "$IN" \
    -af "${VOICE},loudnorm=I=-14:TP=-1.2:LRA=2,alimiter=limit=0.87:level=disabled" \
    -c:v copy -c:a aac -b:a 192k -ar 48000 "$OUT"
fi

echo "--- natija ---"
ffmpeg -hide_banner -i "$OUT" -af ebur128 -f null - 2>&1 \
  | sed -n '/Summary/,/LRA high/p' | grep -E "I:|LRA:|Threshold" | head -4
