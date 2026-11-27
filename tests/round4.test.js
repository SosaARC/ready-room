const {JSDOM}=require('jsdom');const fs=require('fs');
const html=fs.readFileSync(process.argv[2],'utf8');const starter=fs.readFileSync(process.argv[3],'utf8');
const errors=[];
const dom=new JSDOM(html,{runScripts:'dangerously',url:'https://example.org/',pretendToBeVisual:true,beforeParse(w){
  w.scrollTo=()=>{};
  const sample=async()=>({text:''});sample.limits=async()=>({images:false});
  sample.json=async p=>{if(p.startsWith('These are recent emails'))return {items:[{email:0,broker:'TQL',status:'Approved',carrierId:'TQ-778',note:'Carrier setup approved'},{email:1,broker:'Echo Global Logistics',status:'Action needed',carrierId:'',note:'Upload W-9'}]};return {}};
  const mcp={callTool:async()=>({payload:{threads:[{id:'a',messages:[{subject:'Your TQL carrier setup is approved',sender:'carriers@tql.com'}]},{id:'b',messages:[{subject:'Action required: RMIS profile',sender:'noreply@rmis.com'}]}]}})};
  w.claude={use:async n=>({sample,mcp})[n]||null};
}});
const w=dom.window;w.addEventListener('error',e=>errors.push(e.message));
const sleep=ms=>new Promise(r=>setTimeout(r,ms));const $=s=>w.document.querySelector(s);const $$=s=>[...w.document.querySelectorAll(s)];
const click=el=>{el=typeof el==='string'?$(el):el;el.dispatchEvent(new w.MouseEvent('click',{bubbles:true,cancelable:true}))};
const check=(n,c)=>console.log((c?'PASS ':'FAIL ')+n);
(async()=>{await sleep(300);
 // restore starter via the internal restore path (paste form)
 click('[data-act=loadSample]');await sleep(60);w.location.hash='data';await sleep(60);
 click('[data-act=importBiz]');await sleep(20);$('#imp').value=starter;$('#importForm').dispatchEvent(new w.Event('submit',{bubbles:true,cancelable:true}));await sleep(80);
 check('starter loaded',$('#bizSel').selectedOptions[0].textContent==='5908 Logistics');
 check('setup card shown',$('#view').textContent.includes('Get set up'));
 check('authority age shown',/Authority active \d+ days/.test($('#view').textContent));
 w.location.hash='brokers';await sleep(60);
 check('10 setups',$$('#view .card h3').length>=10);
 click('[data-act=approvalScan]');await sleep(120);
 check('approval suggestions',$('#view').textContent.includes('From your inbox (2)'));
 click($$('[data-act=apAccept]')[0]);await sleep(40);
 const tqlCard=$$('#view .card').find(c=>c.querySelector('h3')&&c.querySelector('h3').textContent==='TQL');
 check('TQL approved with id',tqlCard&&tqlCard.textContent.includes('Approved')&&tqlCard.querySelector('[data-bf=carrierId]').value==='TQ-778');
 click($$('[data-act=apAdd]')[0]);await sleep(40);check('new setup added',$$('#view .card h3').some(h=>h.textContent.includes('Echo')));
 // reuse answers
 w.location.hash='answers';await sleep(60);
 const sel=$('select[data-reuse=desc_short]');check('reuse select offered',!!sel);
 console.log('ERRORS:',errors.length?errors:'none');process.exit(0)})();
