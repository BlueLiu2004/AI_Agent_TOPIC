import fs from 'node:fs';
import path from 'node:path';
import {bundle} from '@remotion/bundler';
import {openBrowser,selectComposition,renderMedia} from '@remotion/renderer';

// No dotenv loader, application imports, or AI/search API calls.
const browserExecutable=process.env.REMOTION_BROWSER||(fs.existsSync('C:/Program Files/Google/Chrome/Application/chrome.exe')?'C:/Program Files/Google/Chrome/Application/chrome.exe':undefined);
fs.mkdirSync('out',{recursive:true});
const serveUrl=await bundle({entryPoint:path.resolve('src/index.ts'),outDir:path.resolve('.cache/bundle')});
const browser=await openBrowser('chrome',{browserExecutable});
let last=-1;
const started=Date.now();
const segment=process.argv.includes('--recap-only');
try{
 const composition=await selectComposition({serveUrl,id:'OnboardBot',puppeteerInstance:browser});
 await renderMedia({
  serveUrl,composition,puppeteerInstance:browser,
  codec:'h264',pixelFormat:'yuv420p',crf:18,concurrency:4,
  outputLocation:path.resolve(segment?'out/recap-correction.mp4':'out/onboardbot-tutorial.mp4'),
  ...(segment?{frameRange:[5340,5759]}:{}),
  onProgress:({progress,renderedFrames,encodedFrames})=>{
   const p=Math.floor(progress*20)*5;
   if(p!==last){last=p;console.log(JSON.stringify({percent:p,renderedFrames,encodedFrames,elapsedSeconds:Math.round((Date.now()-started)/1000)}));}
  }
 });
 console.log('Render complete:',segment?'out/recap-correction.mp4':'out/onboardbot-tutorial.mp4');
}finally{await browser.close({silent:true});}
