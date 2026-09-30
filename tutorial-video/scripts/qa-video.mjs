import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
const file='out/onboardbot-tutorial.mp4';
fs.mkdirSync('qa',{recursive:true});
function run(bin,args){
 const r=spawnSync(bin,args,{encoding:'utf8',maxBuffer:20e6});
 if(r.status!==0)throw Error(r.stderr||r.error?.message||bin+' failed');
 return r;
}
if(!fs.existsSync(file))throw Error('MP4 not found');
const info=JSON.parse(run('ffprobe',['-v','error','-show_format','-show_streams','-of','json',file]).stdout);
fs.writeFileSync('qa/media-info.json',JSON.stringify(info,null,2));
const v=info.streams.find(s=>s.codec_type==='video'),a=info.streams.find(s=>s.codec_type==='audio');
if(v.width!==1920||v.height!==1080||v.avg_frame_rate!=='30/1'||Number(v.nb_frames)!==5760)throw Error('Unexpected video dimensions/rate/frames');
if(Math.abs(Number(info.format.duration)-192)>0.1||!a)throw Error('Missing duration/audio');
console.log('PASS dimensions, duration, frame count, and audio stream');
const decode=run('ffmpeg',['-hide_banner','-i',file,'-vf','blackdetect=d=0.1:pix_th=0.01:pic_th=0.98','-af','volumedetect','-f','null','-']);
fs.writeFileSync('qa/decode-check.txt',decode.stderr);
if(decode.stderr.includes('black_start:'))throw Error('Detected black interval');
const volume=decode.stderr.match(/mean_volume:\s*(-?[\d.]+) dB/);
if(!volume||Number(volume[1]) < -50)throw Error('Missing or unexpectedly silent narration');
console.log('PASS full decode, no detected black intervals, mean audio volume',volume[1]+' dB');
const times=[4,20,40,81,96,110,128,146,169,186];
for(const t of times){
 run('ffmpeg',['-hide_banner','-loglevel','error','-y','-ss',String(t),'-i',file,'-frames:v','1','qa/final-'+String(t).padStart(3,'0')+'.png']);
 console.log('Extracted actual MP4 frame at',t,'seconds');
}
fs.writeFileSync('qa/media-check.json',JSON.stringify({
 checkedAt:new Date().toISOString(),width:v.width,height:v.height,fps:v.avg_frame_rate,
 frames:Number(v.nb_frames),duration:Number(info.format.duration),
 videoCodec:v.codec_name,audioCodec:a.codec_name,bytes:Number(info.format.size),
 fullDecode:'passed',detectedBlackIntervals:0,meanVolumeDb:Number(volume[1]),sampleSeconds:times
},null,2));
