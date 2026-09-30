import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import source from './data/source.json';

export const C={bg:'#08111f',panel:'#111f31',line:'#2b3e55',text:'#eff6ff',muted:'#93a9c4',green:'#50dfb2',blue:'#65b7ff',gold:'#ffcb70',red:'#ff8d95'};
export const mono={fontFamily:'JetBrains, monospace'};
export const Pill:React.FC<{children:React.ReactNode;color?:string}>=({children,color=C.blue})=><span style={{display:'inline-block',padding:'9px 18px',fontSize:24,borderRadius:10,color,background:color+'16',border:'1px solid '+color+'44'}}>{children}</span>;
export const Panel:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style})=><div style={{background:C.panel,border:'1px solid '+C.line,borderRadius:22,padding:30,minWidth:0,width:'100%',...style}}>{children}</div>;
export const Label:React.FC<{children:React.ReactNode;color?:string}>=({children,color=C.muted})=><div style={{fontSize:24,color,marginBottom:14,...mono}}>{children}</div>;
export const QuestionCard:React.FC<{children:React.ReactNode;style?:React.CSSProperties}>=({children,style})=><div style={{padding:'22px 30px',borderLeft:'5px solid '+C.gold,background:'#182536',borderRadius:12,fontSize:34,lineHeight:1.55,...style}}>{children}</div>;
export const CodePanel:React.FC<{id:keyof typeof source.snippets;active?:number[];fontSize?:number;note?:string}>=({id,active=[],fontSize=25,note})=>{
 const s=source.snippets[id];
 const indent=Math.min(...s.lines.filter(l=>l.trim()).map(l=>(l.match(/^ */)?.[0].length??0)));
 return <Panel style={{height:'100%',padding:0,overflow:'hidden'}}>
   <div style={{borderBottom:'1px solid '+C.line,padding:'18px 24px',display:'flex',justifyContent:'space-between',fontSize:23,...mono}}><span>{s.file}</span><span style={{color:C.muted}}>L{s.first}–{s.last} · 原始碼節錄</span></div>
   <div style={{padding:'16px 0'}}>
    {s.lines.map((line,i)=><div key={i} style={{display:'flex',padding:'3px 22px',lineHeight:1.3,fontSize,...mono,color:active.length&&!active.includes(i)?'#8497ae':C.text,background:active.includes(i)?'#254360':'transparent',borderLeft:'4px solid '+(active.includes(i)?C.blue:'transparent')}}>
      <span style={{flex:'0 0 48px',fontSize:20,color:'#677e99',userSelect:'none'}}>{s.first+i}</span>
      <span style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere',minWidth:0}}>{line.slice(indent)||' '}</span>
    </div>)}
   </div>
   {note&&<div style={{fontSize:26,color:C.gold,padding:'0 28px 25px',lineHeight:1.5}}>{note}</div>}
 </Panel>
};

export const StateInspector:React.FC<{rows:{key:string;value:React.ReactNode;color?:string}[];title?:string;style?:React.CSSProperties}>=({rows,title='STATE INSPECTOR',style})=><Panel style={{height:'100%',...style}}>
 <Label color={C.blue}>{title}</Label>
 {rows.map((r,i)=><div key={i} style={{padding:'17px 0',borderBottom:i<rows.length-1?'1px solid '+C.line:'none'}}>
  <div style={{fontSize:23,color:C.muted,...mono,marginBottom:8}}>{r.key}</div>
  <div style={{fontSize:31,color:r.color??C.text,lineHeight:1.45,overflowWrap:'anywhere'}}>{r.value}</div>
 </div>)}
</Panel>;

export const DataToken:React.FC<{progress:number}>=({progress})=>{
 const x=interpolate(progress,[0,1],[384,144],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 const y=interpolate(progress,[0,1],[-4,57],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 return <div style={{position:'absolute',left:x,top:y,padding:'3px 8px',fontSize:30,fontWeight:800,background:C.gold,color:C.bg,borderRadius:9,boxShadow:'0 8px 28px #0005',...mono}}>22</div>
};
export const TraceTimeline:React.FC<{items:string[];active:number}>=({items,active})=><div style={{display:'flex',gap:12,flexWrap:'wrap'}}>{items.map((x,i)=><span key={x} style={{fontSize:24,...mono,color:i<=active?C.green:C.muted}}>{i>0?'→ ':''}{x}</span>)}</div>;

type NodeBox={x:number;y:number;w:number;h:number};
const fullNodes:Record<string,NodeBox>={
 START:{x:485,y:10,w:120,h:42},router:{x:435,y:90,w:220,h:60},
 retrieve:{x:205,y:225,w:260,h:60},grade_documents:{x:195,y:350,w:280,h:62},
 rewrite_query:{x:30,y:475,w:245,h:60},build_web_query:{x:705,y:235,w:315,h:60},
 tavily_search:{x:720,y:365,w:285,h:60},generate:{x:565,y:515,w:240,h:60},
 fallback_generate:{x:190,y:585,w:310,h:60},END:{x:625,y:630,w:140,h:40},
};
const fullPaths:Record<string,{d:string;label?:string;x?:number;y?:number}>={
 'START>router':{d:'M545 52 V90'},
 'router>retrieve':{d:'M435 120 H335 V225',label:'internal / hybrid',x:220,y:183},
 'router>build_web_query':{d:'M655 120 H862 V235',label:'external',x:785,y:183},
 'retrieve>grade_documents':{d:'M335 285 V350'},
 'grade_documents>generate':{d:'M475 391 H530 V545 H565',label:'相關／internal',x:432,y:453},
 'grade_documents>build_web_query':{d:'M475 370 H615 V265 H705',label:'relevant + hybrid',x:510,y:322},
 'grade_documents>rewrite_query':{d:'M195 382 H153 V475',label:'不相關，可重試',x:127,y:446},
 'rewrite_query>retrieve':{d:'M30 505 H10 V255 H205',label:'回到檢索',x:95,y:319},
 'grade_documents>fallback_generate':{d:'M335 412 V585',label:'不相關且達上限',x:228,y:568},
 'build_web_query>tavily_search':{d:'M862 295 V365'},
 'tavily_search>generate':{d:'M862 425 V487 H685 V515'},
 'generate>END':{d:'M685 575 V630'},
 'fallback_generate>END':{d:'M500 615 H565 V650 H625'},
};
export const ArchitectureGraph:React.FC<{variant?:'hybrid'|'full';active?:string;done?:string[];allLit?:boolean}>=({variant='full',active='',done=[],allLit=false})=>{
 const frame=useCurrentFrame();
 const steps=['router','retrieve','grade_documents','build_web_query','tavily_search','generate'];
 const boxes:Record<string,NodeBox>=variant==='full'?fullNodes:Object.fromEntries(steps.map((s,i)=>[s,{x:150,y:20+i*98,w:435,h:64}]));
 const paths:Record<string,{d:string;label?:string;x?:number;y?:number}>=variant==='full'?fullPaths:Object.fromEntries(steps.slice(1).map((s,i)=>[steps[i]+'>'+s,{d:`M367 ${84+i*98} V${118+i*98}`}]));
 const known=new Set(source.graph.edges.map(e=>e.from+'>'+e.to));
 const width=variant==='full'?1050:735, height=variant==='full'?690:600;
 return <svg viewBox={`0 0 ${width} ${height}`} style={{width:'100%',height:'100%',overflow:'visible'}}>
 <defs><marker id={'arrow-'+variant} markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill={C.muted}/></marker><marker id={'lit-'+variant} markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill={C.gold}/></marker></defs>
 {Object.entries(paths).filter(([key])=>known.has(key)).map(([key,p])=>{
  const [a,b]=key.split('>');const lit=allLit||done.includes(a)&& (done.includes(b)||active===b);
  return <g key={key}><path d={p.d} fill="none" stroke={lit?C.gold:'#46617e'} strokeWidth={lit?3.5:2.5} markerEnd={`url(#${lit?'lit':'arrow'}-${variant})`} strokeDasharray={a==='rewrite_query'?'9 7':undefined}/>{'label'in p&&p.label&&<text x={p.x} y={p.y} textAnchor="middle" fill={lit?C.gold:C.muted} fontSize={22} fontFamily="Noto">{p.label}</text>}</g>;
 })}
 {Object.entries(boxes).map(([name,n])=>{
  const lit=allLit||done.includes(name), now=active===name;
  const color=name==='fallback_generate'?C.red:name==='build_web_query'||name==='tavily_search'?C.blue:C.green;
  return <g key={name} transform={`translate(${n.x},${n.y})`}>
   <rect width={n.w} height={n.h} rx={12} fill={now?'#2c362e':lit?'#173047':C.panel} stroke={now?C.gold:lit?color:C.line} strokeWidth={now?3.5:2}/>
   {now&&<rect x={-6} y={-6} width={n.w+12} height={n.h+12} rx={16} fill="none" stroke={C.gold} opacity={0.3+0.1*Math.sin(frame/8)}/>}
   <text x={n.w/2} y={n.h/2+9} fill={now?C.gold:lit?C.text:C.muted} textAnchor="middle" fontSize={variant==='full'?25:29} fontFamily="JetBrains">{name}</text>
  </g>
 })}
 </svg>
};

export const SourcePanel:React.FC<{phase:number}>=({phase})=><Panel style={{height:'100%',display:'flex',flexDirection:'column',gap:20}}>
 <Label color={C.blue}>來源約束的三個層次</Label>
 {[
  ['01','集中呼叫','tavily_search_node 取得並呼叫 MCP 工具',C.blue],
  ['02','限制網域','Node.js → nodejs.org；正常 JSON 結果再次過濾 hostname',C.green],
  ['03','核對網址','回答中辨識到的 URL，必須存在於 web_urls',C.gold],
 ].map((r,i)=><div key={i} style={{opacity:phase>=i?1:0.35,display:'flex',gap:20}}>
  <span style={{fontSize:32,color:r[3],...mono,flexShrink:0}}>{r[0]}</span><div style={{minWidth:0,flex:1,overflowWrap:'anywhere'}}><div style={{fontSize:32,fontWeight:700,marginBottom:8}}>{r[1]}</div><div style={{fontSize:25,color:C.muted,lineHeight:1.4}}>{r[2]}</div></div>
 </div>)}
 <div style={{marginTop:'auto',fontSize:23,color:C.gold,lineHeight:1.4}}>來源一致性 ≠ 內容正確性<br/>非 JSON fallback 沒有同樣的二次網域檢查</div>
</Panel>;
