import React from 'react';
import {interpolate} from 'remotion';
import {ArchitectureGraph,C,CodePanel,DataToken,Label,mono,Panel,Pill,QuestionCard,SourcePanel,StateInspector,TraceTimeline} from './components';

export const Hook:React.FC<{t:number}>=({t})=><div>
 <QuestionCard style={{fontSize:49,padding:36,textAlign:'center'}}>公司要求使用哪一版 Node.js？<br/>給我該版的官方下載網址。</QuestionCard>
 <div style={{display:'flex',alignItems:'center',justifyContent:'center',gap:42,marginTop:50}}>
  <Panel style={{width:520,textAlign:'center',borderColor:C.green}}><div style={{fontSize:26,color:C.green,marginBottom:15}}>INTERNAL KNOWLEDGE</div><div style={{fontSize:43,fontWeight:700}}>公司指定版本</div><div style={{fontSize:27,color:C.muted,marginTop:14}}>來自企業內部政策</div></Panel>
  <span style={{fontSize:68,color:C.muted}}>＋</span>
  <Panel style={{width:520,textAlign:'center',borderColor:C.blue}}><div style={{fontSize:26,color:C.blue,marginBottom:15}}>PUBLIC WEB</div><div style={{fontSize:43,fontWeight:700}}>官方下載資訊</div><div style={{fontSize:27,color:C.muted,marginTop:14}}>來自公開搜尋來源</div></Panel>
 </div>
 <div style={{marginTop:35,textAlign:'center',fontSize:31,color:C.gold,opacity:Math.min(1,t/1.2)}}>先選資料來源，再整合回答</div>
 <div style={{textAlign:'center',color:C.muted,fontSize:23,marginTop:17}}>TechCore 與政策皆為虛構示範</div>
</div>;

export const Routes:React.FC<{t:number}>=({t})=>{
 const active=t<5.5?0:t<11?1:t<16.5?2:3;
 const items=[
  {name:'internal',color:C.green,sub:'只需公司內部依據',q:'公司的遠端工作政策是什麼？',path:['retrieve','grade_documents','generate'],foot:'企業內部 Chroma'},
  {name:'external',color:C.blue,sub:'只需公開資訊',q:'目前 Node.js 官方最新 LTS 是哪一版？',path:['build_web_query','tavily_search','generate'],foot:'直接搜尋，不必先查內部'},
  {name:'hybrid',color:C.gold,sub:'內部規範＋公開資訊',q:'公司要求哪一版 Node.js？給我官方下載網址。',path:['retrieve → grade','build_web_query','tavily_search → generate'],foot:'先取內部依據，再搜尋'},
 ];
 return <div>
  <div style={{fontSize:31,textAlign:'center',marginBottom:27,...mono}}>Question <span style={{color:C.muted}}>→</span> <span style={{color:C.gold}}>Router</span> <span style={{fontFamily:'Noto',fontSize:25,color:C.muted}}>　依問題選一路</span></div>
  <div style={{display:'flex',gap:24}}>{items.map((r,i)=><Panel key={r.name} style={{width:576,height:470,borderColor:active===i||active===3?r.color:C.line,opacity:active===i||active===3?1:0.52,boxShadow:active===i?'0 0 0 3px '+r.color+'18':undefined}}>
    <div style={{fontSize:39,color:r.color,fontWeight:700,...mono}}>{r.name}</div>
    <div style={{fontSize:27,margin:'12px 0 24px',color:C.muted}}>{r.sub}</div>
    <div style={{fontSize:31,lineHeight:1.5,minHeight:95}}>{r.q}</div>
    <div style={{marginTop:22,paddingTop:20,borderTop:'1px solid '+C.line,...mono,fontSize:24,lineHeight:1.45}}>{r.path.map((p,j)=><div key={p}>{j>0?'↓ ':''}{p}</div>)}</div>
    <div style={{fontSize:23,color:r.color,marginTop:15}}>{r.foot}</div>
  </Panel>)}</div>
  <div style={{fontSize:27,color:C.muted,textAlign:'center',marginTop:24}}>Node＝處理資料　　Edge＝連到下一步</div>
 </div>
};

export const StateScene:React.FC<{t:number}>=({t})=>{
 const routing=t>=10;
 return <div style={{display:'grid',gridTemplateColumns:'1040px 704px',gap:32,height:620}}>
 <CodePanel id={t>=15?'edges':routing?'routing':'state'} active={routing?(t>=15?[0,1,2,3,4]:[4,5,6,7,8,9]):(t<5?[0,1,2]:[0,1])} fontSize={routing?23:27} note={routing?'Conditional Edge：依 State 決定後續節點；trace 留下執行紀錄。':'節點只回傳需要更新的欄位；其餘資料持續保留。'}/>
 <StateInspector rows={routing?[
  {key:'route',value:'hybrid',color:C.gold},
  {key:'doc_grade',value:'relevant',color:C.green},
  {key:'下一步',value:'build_web_query',color:C.blue},
  {key:'trace',value:'router → retrieve → grade',color:C.muted},
 ]:[
  {key:'original_question',value:'公司要求哪版 Node.js？',color:C.gold},
  {key:'question',value:'公司要求哪版 Node.js？'},
  {key:'route',value:'hybrid',color:C.green},
  {key:'retry_count',value:'0'},
 ]}/>
 </div>
};

export const HybridScene:React.FC<{t:number}>=({t})=>{
 const steps=['router','retrieve','retrieve','grade_documents','build_web_query','tavily_search','generate'];
 const step=t<6.5?0:t<12.5?1:t<18.5?2:t<24.5?3:t<31.5?4:t<38.5?5:6;
 const graphSteps=['router','retrieve','grade_documents','build_web_query','tavily_search','generate'];
 const active=steps[step], done=graphSteps.slice(0,graphSteps.indexOf(active));
 const transfer=step===4&&t<28.5;
 const focusKey=step<3?'documents':step===3?'internal_context':step===4?'web_query':step===5?'web_urls':'final_answer';
 const focusContent=step<2?<span style={{color:C.muted}}>等待檢索結果…</span>:step===2?<><div style={{fontSize:36,color:C.green}}>Node.js 22.11.0</div><div style={{fontSize:28,marginTop:15}}>公司示範政策 it-01 已進入 documents。<br/>下一步先評估相關性。</div></>:step===3?<><div style={{fontSize:31,lineHeight:1.7}}>「TechCore 前端標準開發環境<br/>要求使用 <b style={{color:C.gold}}>Node.js 22.11.0</b>」</div><div style={{fontSize:23,marginTop:18,color:C.muted}}>原文節錄 · relevant 後才寫入此欄位</div></>:step===4?<div style={{position:'relative',height:194}}><div style={{fontSize:24,color:C.muted,...mono}}>internal_context · Node.js <span style={{color:C.gold}}>22.11.0</span></div><div style={{fontSize:30,lineHeight:1.5,...mono,marginTop:24}}>Node.js <b style={{color:C.gold,opacity:transfer?0.2:1}}>22</b> official download<br/>site:nodejs.org</div><div style={{fontSize:23,color:C.gold,marginTop:8}}>從政策擷取主版本：22.11.0 → 22</div>{transfer&&<DataToken progress={interpolate(t,[24.5,28],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}/>}</div>:step===5?<><div style={{fontSize:24,color:C.blue,...mono,lineHeight:1.8}}>nodejs.org/id/blog/release/v22.11.0<br/>nodejs.org/en/download/archive/v12.22.1</div><div style={{fontSize:26,color:C.gold,marginTop:14}}>第二筆版本不符，仍需核對內容。</div><div style={{fontSize:21,color:C.muted,marginTop:10}}>09/25 留存搜尋結果 · URL 省略 https://</div></>:<><div style={{display:'flex',gap:22}}>
 <div style={{width:'49%',padding:10,borderLeft:'4px solid '+C.green}}><div style={{fontSize:28,color:C.green}}>公司內部規範</div><div style={{fontSize:28,marginTop:12}}>依 it-01 說明<br/>公司指定版本</div></div>
 <div style={{width:'49%',padding:10,borderLeft:'4px solid '+C.blue}}><div style={{fontSize:28,color:C.blue}}>外部公開資訊</div><div style={{fontSize:28,marginTop:12}}>搜尋內容另列<br/>附上 web_urls</div></div></div><div style={{fontSize:22,color:C.muted,marginTop:8}}>回答結構示意；不是已查證的最新版結論</div></>;
 return <div style={{display:'grid',gridTemplateColumns:'720px 1024px',gap:32,height:620}}>
  <div><div style={{textAlign:'center',marginBottom:12}}><Pill color={C.gold}>RAG → State → MCP</Pill></div><div style={{height:555}}><ArchitectureGraph variant="hybrid" active={active} done={done}/></div></div>
  <Panel style={{position:'relative',height:620,padding:28}}>
   <div style={{display:'flex',justifyContent:'space-between'}}><Label color={C.blue}>STATE INSPECTOR</Label><span style={{fontSize:21,color:C.muted}}>目前原始碼＋留存紀錄</span></div>
   <div style={{fontSize:23,color:C.muted,...mono}}>original_question</div><div style={{fontSize:29,lineHeight:1.5,marginTop:8}}>公司要求使用哪一版 Node.js？<br/>給我該版的官方下載網址。</div>
   <div style={{display:'flex',gap:44,padding:'20px 0',marginTop:12,borderTop:'1px solid '+C.line,borderBottom:'1px solid '+C.line}}>
    <div><Label>route</Label><span style={{fontSize:30,color:C.gold}}>hybrid</span></div>
    <div><Label>doc_grade</Label><span style={{fontSize:30,color:step>=3?C.green:C.muted}}>{step>=3?'relevant':'尚未評分'}</span></div>
    <div><Label>retry_count</Label><span style={{fontSize:30}}>0</span></div>
   </div>
   <div style={{paddingTop:24}}><Label color={step>=4?C.blue:C.green}>{focusKey}</Label><div style={{minHeight:170,lineHeight:1.5}}>{focusContent}</div></div>
</Panel>
 </div>
};

export const CorrectiveScene:React.FC<{t:number}>=({t})=>{
 const phase=t<6.5?0:t<12.5?1:t<18.5?2:t<25?3:4;
 const nodes=[{n:'retrieve',x:105,y:100,w:290},{n:'grade_documents',x:545,y:100,w:340},{n:'rewrite_query',x:545,y:280,w:340},{n:'generate',x:105,y:445,w:290},{n:'fallback_generate',x:515,y:445,w:370}];
 const active=phase===0?'grade_documents':phase===1?'rewrite_query':phase===2?'retrieve':phase===3?'generate':'fallback_generate';
 const pathColor=(p:number)=>phase===p?C.gold:'#52667f';
 return <div style={{display:'grid',gridTemplateColumns:'990px 754px',gap:32,height:620}}>
  <div><div style={{display:'flex',gap:14,alignItems:'center'}}><Pill color={C.gold}>可控測試示範</Pill><span style={{fontSize:23,color:C.muted}}>tests/test_workflow.py</span></div>
   <svg viewBox="0 0 990 560" style={{width:'100%',height:550,marginTop:12}}>
    <defs><marker id="loopArrow" refX="7" refY="4" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0 L8 4 L0 8" fill={C.gold}/></marker></defs>
    <path d="M395 135 H545" fill="none" stroke={pathColor(0)} strokeWidth="4" markerEnd="url(#loopArrow)"/>
    <path d="M715 170 V280" fill="none" stroke={pathColor(1)} strokeWidth="4" markerEnd="url(#loopArrow)"/>
    <text x="735" y="230" fill={C.red} fontSize="25" textAnchor="start">not_relevant</text>
    <path d="M545 315 H250 V170" fill="none" stroke={pathColor(2)} strokeWidth="5" markerEnd="url(#loopArrow)" strokeDasharray={phase===2?undefined:'12 8'}/>
    <text x="300" y="365" fill={C.gold} fontSize="31" textAnchor="middle">rewrite_query → retrieve</text>
    <path d="M885 135 H950 V390 H250 V445" fill="none" stroke={pathColor(3)} strokeWidth="3" markerEnd="url(#loopArrow)"/>
    <text x="910" y="285" fill={C.green} fontSize="25" textAnchor="middle" transform="rotate(90,910,285)">relevant</text>
    <path d="M830 170 V250 H490 V425 H700 V445" fill="none" stroke={pathColor(4)} strokeWidth="3" strokeDasharray="6 6" markerEnd="url(#loopArrow)"/>
    {nodes.map(n=><g key={n.n}><rect x={n.x} y={n.y} width={n.w} height={70} rx={14} fill={C.panel} stroke={active===n.n?C.gold:C.line} strokeWidth={active===n.n?4:2}/><text x={n.x+n.w/2} y={n.y+44} fill={active===n.n?C.gold:C.text} fontFamily="JetBrains" fontSize="28" textAnchor="middle">{n.n}</text></g>)}
    {phase===4&&<text x="700" y="552" fill={C.red} fontSize="26" textAnchor="middle">仍不相關 ＋ retry_count ≥ 2</text>}
   </svg>
  </div>
  <StateInspector title={phase===4?'另一分支：重試耗盡':'CONTROLLED STATE'} rows={[
   {key:'original_question',value:'公司允許 telecommuting 嗎？',color:C.muted},
   {key:'question',value:phase===0?'公司允許 telecommuting 嗎？':'遠端工作政策',color:phase>0?C.gold:C.text},
   {key:'retry_count',value:phase===0?'0':phase===4?'2（上限）':'0 → 1',color:C.gold},
   {key:'doc_grade / 下一步',value:phase===3?'relevant → generate':phase===4?'not_relevant → fallback':'not_relevant → 改寫／重試',color:phase===3?C.green:C.red},
  ]}/>
 </div>
};

export const McpScene:React.FC<{t:number}>=({t})=><div style={{display:'grid',gridTemplateColumns:'1050px 694px',gap:32,height:620}}>
 <div>{t<12?<Panel style={{height:620}}>
  <Label color={C.blue}>nodes.py · tavily_search_node</Label>
  <div style={{fontSize:33,lineHeight:1.5}}>MCP：連接應用程式與工具的協定</div>
  <div style={{display:'flex',flexDirection:'column',alignItems:'center',marginTop:26,gap:12}}>
  {['MultiServerMCPClient','get_tools()','tavily_search → ainvoke(args)'].map((text,i)=><React.Fragment key={text}>{i>0&&<div style={{fontSize:30,color:C.blue}}>↓</div>}<div style={{border:'1px solid '+C.blue+'77',padding:'20px 30px',fontSize:31,...mono,borderRadius:14,minWidth:700,textAlign:'center',color:i===2?C.gold:C.text}}>{text}</div></React.Fragment>)}
  </div><div style={{fontSize:27,color:C.muted,marginTop:25,textAlign:'center'}}>MCP 負責連接；Tavily 提供搜尋。</div>
 </Panel>:<CodePanel id="urls" active={t<18?[0,1]:[4,5]} fontSize={25} note="保留搜尋回傳的網址；比對不會判斷頁面內容是否正確。"/>}</div>
 <SourcePanel phase={t<6?0:t<12?1:2}/>
</div>;

export const TestScene:React.FC<{t:number}>=({t})=><div style={{display:'grid',gridTemplateColumns:'1010px 734px',gap:32,height:620}}>
 <CodePanel id="retryTest" active={[3,4,5,6,7]} fontSize={23} note="以替身模型、向量庫與 MCP 工具，檢查真正的圖分支。"/>
 <div>
  <Panel style={{height:205,display:'flex',alignItems:'center',gap:32}}>
   <div style={{fontSize:70,fontWeight:800,color:C.green,...mono}}>14/14</div><div><div style={{fontSize:32,fontWeight:700}}>可控測試通過</div><div style={{fontSize:23,color:C.muted,marginTop:12,lineHeight:1.5}}>三路／retry／fallback<br/>工具失敗／格式／URL</div></div>
  </Panel>
  <div style={{display:'flex',gap:20,marginTop:24}}>
   <Panel style={{width:'50%',height:192,opacity:t>=6?1:0.35}}><Label>2026-09-24</Label><div style={{fontSize:50,color:C.gold,fontWeight:800,...mono}}>3/6</div><div style={{fontSize:24,marginTop:9}}>其餘模型 503</div></Panel>
   <Panel style={{width:'50%',height:192,opacity:t>=11.5?1:0.35}}><Label>2026-09-25</Label><div style={{fontSize:50,color:C.blue,fontWeight:800,...mono}}>6/6</div><div style={{fontSize:24,marginTop:9}}>流程完成，無 503</div></Panel>
  </div>
  <div style={{marginTop:26,borderLeft:'4px solid '+C.gold,paddingLeft:20,fontSize:29,lineHeight:1.6,opacity:t>=11.5?1:0.45}}>仍出現錯誤路由、過時或不相關來源。<br/><span style={{color:C.gold}}>完成 ≠ 回答正確</span></div>
 </div>
</div>;

export const Recap:React.FC<{t:number}>=({t})=><div style={{display:'grid',gridTemplateColumns:'1010px 734px',gap:32,height:620}}>
 <div style={{height:620}}><ArchitectureGraph allLit/></div>
 <div style={{padding:'15px 10px 0 20px'}}>
  {[['01','Router 選來源','內部、外部，或兩者結合',C.green],['02','Corrective RAG 修正檢索','評分 → 改寫 → 有上限地重試',C.blue],['03','Hybrid 傳遞內部依據','公司版本 → web_query → 外部來源',C.gold]].map((r,i)=><div key={i} style={{marginBottom:22,paddingBottom:18,borderBottom:'1px solid '+C.line,opacity:t>=i*3?1:0.4}}>
    <div style={{fontSize:23,color:r[3],...mono,marginBottom:10}}>{r[0]}</div><div style={{fontSize:35,fontWeight:700,marginBottom:12}}>{r[1]}</div><div style={{fontSize:27,color:C.muted}}>{r[2]}</div>
  </div>)}
  <div style={{fontSize:25,...mono,marginTop:8,color:C.text}}>graph.py → state.py → nodes.py</div>
 </div>
</div>;
