#!/usr/bin/env bash
# Presentation videos: each stage's best checkpoint from views A (oblique) and D (close-up), 4 envs / 1 env.
C="docker exec -e PYTHONUNBUFFERED=1 -e DISPLAY= isaac-lab-tuberacking bash -c"; IL=/workspace/isaaclab/isaaclab.sh; PROJ=/workspace/isaaclab/dw_wellplate/WellPlate_RL
OUT=/home/aidev/RL_Twin/RL_DT/_isaaclab_wellplate/results/2026-09-21_presentation; LOGS=/home/aidev/RL_Twin/RL_DT/_isaaclab_wellplate/WellPlate_RL/logs/rsl_rl/wellplate
rec() { # stage task run_glob view num_envs length
  local st=$1 task=$2 run=$3 view=$4 n=$5 len=$6
  $C "cd $PROJ && timeout 900 $IL -p scripts/rsl_rl/play.py --task $task --num_envs $n --headless --video --video_length $len --load_run '$run' --view $view" > $OUT/rec_${st}_${view}.log 2>&1
  docker exec isaac-lab-tuberacking bash -c 'pkill -9 -f play.py; true' >/dev/null 2>&1
  local rd; rd=$(ls -d $LOGS/$run 2>/dev/null | tail -1); local f; f=$(ls -t $rd/videos/play/*.mp4 2>/dev/null | head -1)
  [ -n "$f" ] && cp "$f" $OUT/${st}_view${view}.mp4 && echo "$(date '+%H:%M') $st view $view -> $(basename $OUT/${st}_view${view}.mp4)" || echo "$(date '+%H:%M') $st view $view FAILED (see rec_${st}_${view}.log)"
}
rec reach Wellplate-Reach-v0 '2026-09-20_20-29-24_reach' A 4 400
rec reach Wellplate-Reach-v0 '2026-09-20_20-29-24_reach' D 1 300
rec align Wellplate-Align-v0 '2026-09-20_21-49-34_align' A 4 400
rec align Wellplate-Align-v0 '2026-09-20_21-49-34_align' D 1 300
rec lift  Wellplate-Lift-v0  '2026-09-21_04-38-27_lift'  D 1 300
rec lift  Wellplate-Lift-v0  '2026-09-21_04-38-27_lift'  A 4 400
$C "$IL -p -c \"
import imageio.v2 as iio, glob
for f in sorted(glob.glob('/workspace/isaaclab/dw_wellplate/results/2026-09-21_presentation/*.mp4')):
    r = iio.get_reader(f); n = r.count_frames(); iio.imwrite(f[:-4]+'_mid.png', r.get_data(n//2)); iio.imwrite(f[:-4]+'_end.png', r.get_data(n-5)); print('frames', f.split('/')[-1], n)
\"" 2>&1 | grep frames
echo "$(date '+%H:%M') ALL DONE"
