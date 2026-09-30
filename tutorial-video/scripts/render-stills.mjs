import fs from 'node:fs';
import path from 'node:path';
import {bundle} from '@remotion/bundler';
import {openBrowser,selectComposition,renderStill} from '@remotion/renderer';
const browserExecutable=process.env.REMOTION_BROWSER||(fs.existsSync('C:/Program Files/Google/Chrome/Application/chrome.exe')?'C:/Program Files/Google/Chrome/Application/chrome.exe':undefined);
fs.mkdirSync('qa',{recursive:true});
const serveUrl=await bundle({entryPoint:path.resolve('src/index.ts'),outDir:path.resolve('.cache/bundle')});
const browser=await openBrowser('chrome',{browserExecutable});
try {
 const composition=await selectComposition({serveUrl,id:'OnboardBot',puppeteerInstance:browser});
 const times=process.argv.slice(2).length?process.argv.slice(2).map(Number):[4,20,40,47,69,75,81,89,96,110,120,128,137,146,169,186];
 for(const t of times){
  await renderStill({serveUrl,composition,puppeteerInstance:browser,frame:Math.round(t*30),output:`qa/preview-${String(t).padStart(3,'0')}.png`,imageFormat:'png'});
  console.log('Preview',t,'seconds');
 }
 fs.writeFileSync('qa/composition.json',JSON.stringify(composition,null,2));
} finally {await browser.close({silent:true});}
