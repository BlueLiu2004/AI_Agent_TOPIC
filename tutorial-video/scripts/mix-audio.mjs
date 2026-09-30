import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
const cues=JSON.parse(fs.readFileSync('src/data/cues.json','utf8'));
const args=['-hide_banner','-y']; const filters=[]; const metrics=[];
for(let i=0;i<cues.length;i++){
  const file=`public/audio/raw/cue-${String(i).padStart(2,'0')}.wav`;
  const probe=spawnSync('ffprobe',['-v','error','-show_entries','format=duration','-of','csv=p=0',file],{encoding:'utf8'});
  if(probe.status!==0) throw new Error(probe.stderr);
  const duration=Number(probe.stdout.trim()), slot=cues[i].end-cues[i].start-0.16;
  const speed=Math.max(1,duration/slot);
  if(speed>1.65) throw new Error(`Cue ${i} needs rewriting; speed ${speed}`);
  args.push('-i',file);
  filters.push(`[${i}:a]atempo=${speed.toFixed(6)},atrim=duration=${slot},afade=t=out:st=${Math.max(0,Math.min(duration/speed,slot)-0.04)}:d=0.04,adelay=${Math.round(cues[i].start*1000)}:all=1[a${i}]`);
  metrics.push({index:i,start:cues[i].start,end:cues[i].end,rawDuration:duration,speed,spokenDuration:duration/speed});
}
filters.push(cues.map((_,i)=>`[a${i}]`).join('')+`amix=inputs=${cues.length}:normalize=0,apad,atrim=duration=192,loudnorm=I=-16:TP=-1.5:LRA=11[out]`);
fs.mkdirSync('qa',{recursive:true});
fs.writeFileSync('qa/audio-filter.txt',filters.join(';'));
args.push('-filter_complex_script','qa/audio-filter.txt','-map','[out]','-ar','48000','-ac','1','-c:a','pcm_s16le','public/audio/voiceover.wav');
const run=spawnSync('ffmpeg',args,{encoding:'utf8',maxBuffer:4e6});
if(run.status!==0)throw new Error(run.stderr);
fs.writeFileSync('qa/audio-timing.json',JSON.stringify(metrics,null,2));
console.log(`Voiceover 192s; max local speed adjustment ${Math.max(...metrics.map(x=>x.speed)).toFixed(2)}×`);
