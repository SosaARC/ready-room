const puppeteer=require('puppeteer-core');
(async()=>{const b=await puppeteer.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',args:['--no-sandbox']});const ctx=await b.createBrowserContext();const p=await ctx.newPage();await p.setViewport({width:390,height:844});
await p.goto('file://'+process.argv[2],{waitUntil:'domcontentloaded'});await p.waitForSelector('[data-act=loadSample]:not([disabled])',{timeout:30000});await p.click('[data-act=loadSample]');
for(const v of ['today','all','profile','vault','brokers','grants','answers','pipeline','data']){await p.evaluate(v=>location.hash=v,v);await new Promise(r=>setTimeout(r,200));
const r=await p.evaluate(()=>{const W=innerWidth;const out=[];for(const el of document.querySelectorAll('body *')){const x=el.getBoundingClientRect();if(el.scrollWidth>el.clientWidth+1&&el.clientWidth>0&&!el.closest('.scroll')&&!el.closest('nav')&&getComputedStyle(el).overflowX==='visible')out.push(el.tagName+'.'+el.className+' '+el.scrollWidth+'/'+el.clientWidth+' '+(el.textContent||'').slice(0,40))}return [document.documentElement.scrollWidth,out.slice(0,4)]});console.log(v,r[0],r[1].join(' || '))}
await b.close()})();
