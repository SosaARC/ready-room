const puppeteer=require('puppeteer-core');
(async()=>{const b=await puppeteer.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',args:['--no-sandbox']});const ctx=await b.createBrowserContext();const p=await ctx.newPage();await p.setViewport({width:390,height:844});
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.argv[2],{waitUntil:'domcontentloaded'});await p.waitForSelector('[data-act=loadSample]:not([disabled])',{timeout:30000});await p.click('[data-act=loadSample]');await new Promise(r=>setTimeout(r,200));
await p.evaluate(()=>location.hash='grants');await new Promise(r=>setTimeout(r,200));
await p.click('[data-act=grantSave]');await p.evaluate(()=>location.hash='pipeline');await new Promise(r=>setTimeout(r,200));
await p.click('input[data-pp=deadline]');await p.keyboard.type('12152026');await new Promise(r=>setTimeout(r,200));
const v=await p.evaluate(()=>({val:document.querySelector('input[data-pp=deadline]').value,focus:document.activeElement.dataset.pp}));console.log('date typed:',JSON.stringify(v));
await p.click('input[data-pp=ask]',{clickCount:3});await p.keyboard.type('$12,000');await p.keyboard.press('Tab');await new Promise(r=>setTimeout(r,200));
console.log('after tab focus:',await p.evaluate(()=>document.activeElement.tagName+' '+(document.activeElement.dataset.pp||document.activeElement.textContent.slice(0,20))));
// scroll jump: open checklist and tick
await p.evaluate(()=>{for(const d of document.querySelectorAll('details'))d.open=true});await new Promise(r=>setTimeout(r,100));
await p.type('form.ckAdd input','Signed cover letter');await p.click('form.ckAdd button');await new Promise(r=>setTimeout(r,200));await p.evaluate(()=>{for(const d of document.querySelectorAll('details'))d.open=true});const box=await p.$('input[data-ck]');await box.evaluate(e=>e.scrollIntoView({block:'center'}));const y0=await p.evaluate(()=>scrollY);await box.click();await new Promise(r=>setTimeout(r,200));const y1=await p.evaluate(()=>scrollY);console.log('scroll before/after tick:',y0,y1);
console.log('errors',errs);await b.close()})();
