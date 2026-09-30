import React,{useEffect,useState} from 'react';
import {AbsoluteFill,Audio,cancelRender,continueRender,delayRender,interpolate,staticFile,useCurrentFrame,useVideoConfig} from 'remotion';
import scenes from './data/scenes.json';
import cues from './data/cues.json';
import {C,mono} from './components';
import {Hook,Routes,StateScene,HybridScene,CorrectiveScene,McpScene,TestScene,Recap} from './scenes';

const scenesUI=[Hook,Routes,StateScene,HybridScene,CorrectiveScene,McpScene,TestScene,Recap];
export const CaptionLayer:React.FC<{seconds:number}>=({seconds})=>{
 const cue=cues.find(c=>seconds>=c.start&&seconds<c.end);
 return <div style={{position:'absolute',bottom:47,left:80,right:80,height:139,display:'flex',alignItems:'center',justifyContent:'center',borderRadius:16,background:'#050b14ef',borderTop:'1px solid #314459',padding:'17px 65px'}}>
  <div style={{textAlign:'center',fontSize:36,lineHeight:1.55,fontWeight:500,maxWidth:1580,color:'#fff'}}>{cue?.text??' '}</div>
 </div>;
};
export const Video:React.FC=()=>{
 const frame=useCurrentFrame(),{fps}=useVideoConfig(),seconds=frame/fps;
 const [fontHandle]=useState(()=>delayRender('Load bundled fonts'));
 useEffect(()=>{
  const a=new FontFace('Noto',`url(${staticFile('fonts/NotoSansTC.ttf')})`,{weight:'100 900'});
  const b=new FontFace('JetBrains',`url(${staticFile('fonts/JetBrainsMono.ttf')})`,{weight:'100 800'});
  Promise.all([a.load(),b.load()]).then(fonts=>{fonts.forEach(f=>(document.fonts as FontFaceSet & {add:(font:FontFace)=>void}).add(f));continueRender(fontHandle);}).catch(e=>cancelRender(e));
 },[fontHandle]);
 const index=Math.max(0,scenes.findIndex(s=>seconds>=s.start&&seconds<s.end));
 const scene=scenes[index],t=seconds-scene.start,Body=scenesUI[index];
 const entrance=interpolate(t,[0,0.32],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 return <AbsoluteFill style={{background:C.bg,color:C.text,fontFamily:'Noto, Microsoft JhengHei, sans-serif'}}>
  <style>{'* { box-sizing: border-box; }'}</style>
  <AbsoluteFill style={{backgroundImage:'radial-gradient(ellipse at 85% 0%, #1c355a88, transparent 57%)'}}/>
  <div style={{position:'absolute',left:72,right:72,top:42,display:'flex',alignItems:'center',justifyContent:'space-between',fontSize:25}}>
   <div style={{letterSpacing:2,fontWeight:700}}>ONBOARDBOT <span style={{fontWeight:400,color:C.muted,letterSpacing:0}}>／程式架構速讀</span></div>
   <div style={{color:C.muted}}>{scene.chapter} <span style={{...mono,fontSize:21,marginLeft:35}}>{String(Math.floor(seconds/60)).padStart(2,'0')}:{String(Math.floor(seconds)%60).padStart(2,'0')} / 03:12</span></div>
  </div>
  <div style={{position:'absolute',left:72,top:112,fontSize:54,fontWeight:800,letterSpacing:0.3}}>{scene.title}</div>
  <div style={{position:'absolute',left:74,top:193,fontSize:24,color:C.muted}}>
   {index===0?'LangGraph · Corrective RAG · Tavily MCP':index===4?'這段為測試設定的示範；線上模型不保證每次走相同路徑。':index===6?'留存實驗紀錄；影片製作未重新呼叫線上 AI。':index===7?'圖的節點與邊對照目前 graph.py。':'TechCore 為虛構公司；畫面程式碼取自目前 repository。'}
  </div>
  <div style={{position:'absolute',left:72,right:72,top:256,height:620,opacity:entrance,transform:`translateY(${(1-entrance)*12}px)`}}><Body t={t}/></div>
  <CaptionLayer seconds={seconds}/>
  <div style={{position:'absolute',bottom:18,left:80,right:80,display:'flex',gap:8}}>
   {scenes.map((s,i)=><div key={s.id} style={{height:5,flex:s.end-s.start,background:i<index?C.blue:i===index?C.gold:'#22334b',borderRadius:3}}/>)}
  </div>
  <Audio src={staticFile('audio/voiceover.wav')}/>
 </AbsoluteFill>
};
