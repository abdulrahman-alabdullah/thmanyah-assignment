#!/bin/sh
set -eu
output=${1:-/evidence/local-hevc.ts}
ffmpeg -hide_banner -y \
  -f lavfi -i 'testsrc2=size=1920x1080:rate=25' \
  -f lavfi -i 'anoisesrc=color=pink:sample_rate=48000:amplitude=0.2' \
  -t 10 -c:v libx265 -preset ultrafast -pix_fmt yuv420p \
  -b:v 12M -minrate 12M -maxrate 12M -bufsize 24M \
  -x265-params 'strict-cbr=1:vbv-maxrate=12000:vbv-bufsize=24000:hrd=1:keyint=50:min-keyint=50:scenecut=0:pools=2' \
  -c:a aac -b:a 192k -ar 48000 -ac 2 -f mpegts "$output"
ffprobe -v error -show_streams -show_format -of json "$output"
