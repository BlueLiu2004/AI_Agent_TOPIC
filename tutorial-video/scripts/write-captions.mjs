import fs from 'node:fs';
const cues = JSON.parse(fs.readFileSync('src/data/cues.json', 'utf8'));
const scenes = JSON.parse(fs.readFileSync('src/data/scenes.json', 'utf8'));
const stamp = s => {
  const ms=Math.round(s*1000), h=Math.floor(ms/3600000), m=Math.floor(ms/60000)%60;
  return [h,m,Math.floor(ms/1000)%60].map(v=>String(v).padStart(2,'0')).join(':')+','+String(ms%1000).padStart(3,'0');
};
const breakText = text => {
  if(text.length<=36) return text;
  const target=text.length/2;
  const positions=[...text].map((c,i)=>'，；：。'.includes(c)?i+1:-1).filter(i=>i>10&&i<text.length-10);
  const pos=positions.sort((a,b)=>Math.abs(a-target)-Math.abs(b-target))[0]??Math.round(target);
  return text.slice(0,pos)+'\n'+text.slice(pos);
};
fs.writeFileSync('captions.srt', cues.map((c,i)=>`${i+1}\n${stamp(c.start)} --> ${stamp(c.end)}\n${breakText(c.text)}\n`).join('\n'));
let md='# OnboardBot 教學影片逐字稿\n\n全長 192 秒。字幕與旁白時間以 src/data/cues.json 為單一來源。音軌使用本機 Microsoft Hanhan Desktop（zh-TW）。英文識別名稱在字幕保留；語音以相應中文解說，少量產品名保留英文。\n';
for(const s of scenes) {
  md+=`\n## ${s.start}–${s.end} 秒　${s.title}\n\n`;
  for(const c of cues.filter(c=>c.start>=s.start&&c.start<s.end)) {
    md+=`- ${c.start.toFixed(1)}–${c.end.toFixed(1)}：${c.text}\n`;
    if(c.speech&&c.speech!==c.text) md+=`  旁白：${c.speech}\n`;
  }
}
fs.writeFileSync('narration.md',md);
console.log(`Wrote ${cues.length} captions and narration.md`);
