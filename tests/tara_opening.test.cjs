/* Real launch, permission, wait and cancellation handlers, without a real mic. */
const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const tick=()=>new Promise(r=>setImmediate(r));
function setup({dedicated=false,permissionPending=false}={}){
  const nodes=new Map(),calls=[],events=new Map(),recognitions=[],requests=[],timers=new Map();
  let resolveSession,resolvePermission,permissionCalls=0,stoppedTracks=0,clock=0,nextTimer=1;
  function node(id){
    if(!nodes.has(id))nodes.set(id,{id,dataset:{mode:'sandbox'},handlers:{},classList:{toggle(){}},textContent:'',value:'',hidden:false,
      addEventListener(name,fn){this.handlers[name]=fn;},focus(){},replaceChildren(){},append(){},
      showModal(){this.open=true;},close(){this.open=false;this.handlers.close?.();}});
    return nodes.get(id);
  }
  const dialog=node('tara-dialog'),opener=node('opener');
  class Speech{
    setRecovery(audio){calls.push(['prepare-recovery',audio.id]);}setWelcome(audio){calls.push(['prepare',audio.id]);}setThinking(audio){calls.push(['prepare-thinking',audio.id]);}
    play(id,mode,done){calls.push(['play',id,mode,done]);return Promise.resolve(true);}
    playThinking(){calls.push(['thinking']);return Promise.resolve(true);}
    cancel(){calls.push(['cancel']);}prime(){return Promise.resolve(true);}
  }
  class Recognition{
    constructor(){recognitions.push(this);}start(){this.started=true;}abort(){this.aborted=true;}stop(){this.onend?.();}
  }
  const document={hidden:false,getElementById:id=>id==='tara-dialog'&&dedicated?null:node(id),
    querySelector:selector=>selector.startsWith('meta')?{content:'test'}:null,
    querySelectorAll:selector=>selector==='[data-tara-open]'?[opener]:[],
    addEventListener:(name,fn)=>events.set(name,fn),createElement:()=>node('created-'+nodes.size)};
  const window={TaraAudio:Speech,SpeechRecognition:Recognition,addEventListener:(name,fn)=>events.set(name,fn),MediaRecorder:null};
  const result=text=>({history:[{role:'assistant',text,id:text==='Welcome'?'welcome':'answer'}],resources:[],fields:{},sandbox_ready:true});
  const context={document,window,location:{pathname:dedicated?'/tara':'/'},
    navigator:{mediaDevices:{getUserMedia(){permissionCalls++;const stream={getTracks:()=>[{stop(){stoppedTracks++;}}]};return permissionPending?new Promise(r=>{resolvePermission=()=>r(stream);}):Promise.resolve(stream);}}},
    sessionStorage:{getItem(){return null;}},
    fetch:(url,options)=>url.includes('/session?')?new Promise(r=>{resolveSession=r;}):new Promise(resolve=>requests.push({url,options,resolve})),
    setTimeout(fn,delay){const id=nextTimer++;timers.set(id,{fn,at:clock+delay});return id;},clearTimeout:id=>timers.delete(id),clearInterval(){}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../static/js/tara.js'),'utf8'),context);
  return{dialog,calls,node,events,document,recognitions,requests,permissionCalls:()=>permissionCalls,stoppedTracks:()=>stoppedTracks,
    click:target=>node(target).handlers.click?.({preventDefault(){}}),
    welcomeEnd:()=>calls.find(c=>c[0]==='play'&&c[1]==='welcome')[3]?.(),
    replyEnd:()=>calls.findLast(c=>c[0]==='play'&&c[1]==='answer')[3]?.(),
    permit:()=>resolvePermission(),ready(){resolveSession({ok:true,json:async()=>result('Welcome')});},
    answer(){requests[0].resolve({ok:true,json:async()=>result('Here is the answer.')});},
    submit(){node('tara-message').value='A detailed question';node('tara-chat-form').handlers.submit({preventDefault(){}});},
    advance(ms){clock+=ms;for(const [id,timer]of [...timers])if(timer.at<=clock){timers.delete(id);timer.fn();}}};
}
test('Page visits are silent and never request microphone permission',()=>{
  for(const dedicated of [false,true]){const s=setup({dedicated});assert.equal(s.permissionCalls(),0);assert.equal(s.calls.filter(c=>c[0]==='play').length,0);}
});
test('Explicit launch welcomes immediately; listening waits for greeting and session',async()=>{
  const s=setup();s.click('opener');assert.equal(s.dialog.open,true);assert.equal(s.permissionCalls(),1);
  assert.equal(s.calls.filter(c=>c[0]==='play').length,1);assert.equal(s.recognitions.length,0);
  s.welcomeEnd();await tick();assert.equal(s.recognitions.length,0);s.ready();await tick();
  assert.equal(s.recognitions.length,1);assert.equal(s.recognitions[0].started,true);assert.equal(s.stoppedTracks(),1);
});
test('A ready session never listens before the welcome ends',async()=>{
  const s=setup();s.ready();await tick();s.click('opener');await tick();assert.equal(s.recognitions.length,0);
  s.welcomeEnd();await tick();assert.equal(s.recognitions.length,1);
});
test('Close during pending permission/session releases a late stream without listening',async()=>{
  const s=setup({permissionPending:true});s.click('opener');s.welcomeEnd();s.click('tara-close');
  s.permit();s.ready();await tick();assert.equal(s.dialog.open,false);assert.equal(s.recognitions.length,0);assert.equal(s.stoppedTracks(),1);
});
test('Reopening explicitly resumes listening without repeating the welcome',async()=>{
  const s=setup();s.ready();await tick();s.click('opener');s.welcomeEnd();await tick();s.click('tara-close');
  assert.equal(s.recognitions[0].aborted,true);s.click('opener');await tick();assert.equal(s.recognitions.length,2);
  assert.equal(s.calls.filter(c=>c[0]==='play'&&c[1]==='welcome').length,1);
});
test('Dedicated Tara starts only after its explicit voice control',async()=>{
  const s=setup({dedicated:true});s.ready();await tick();s.click('tara-voice');s.welcomeEnd();await tick();assert.equal(s.recognitions.length,1);
});
test('Slow voice questions get one acknowledgement and listen again after reply audio',async()=>{
  const s=setup();s.ready();await tick();s.click('opener');s.welcomeEnd();await tick();s.submit();
  s.advance(1499);assert.equal(s.calls.filter(c=>c[0]==='thinking').length,0);s.advance(1);s.advance(5000);
  assert.equal(s.calls.filter(c=>c[0]==='thinking').length,1);s.answer();await tick();
  assert.equal(s.recognitions.length,1);s.replyEnd();await tick();assert.equal(s.recognitions.length,2);
});
test('Fast replies and text-only questions never play waiting acknowledgements',async()=>{
  const s=setup();s.ready();await tick();s.submit();s.advance(2000);assert.equal(s.calls.filter(c=>c[0]==='thinking').length,0);
  s.answer();await tick();assert.equal(s.calls.filter(c=>c[0]==='play').length,0);
  const v=setup();v.ready();await tick();v.click('opener');v.welcomeEnd();await tick();v.submit();v.answer();await tick();v.advance(3000);
  assert.equal(v.calls.filter(c=>c[0]==='thinking').length,0);
});
test('Stop, close, typing and page hide cancel pending acknowledgement and late speech',async()=>{
  for(const action of ['tara-stop','tara-close','tara-text','hidden','pagehide']){
    const s=setup();s.ready();await tick();s.click('opener');s.welcomeEnd();await tick();s.submit();
    if(action==='hidden'){s.document.hidden=true;s.events.get('visibilitychange')();}
    else if(action==='pagehide')s.events.get('pagehide')();else s.click(action);
    s.advance(3000);s.answer();await tick();assert.equal(s.calls.filter(c=>c[0]==='thinking').length,0);
    assert.equal(s.calls.filter(c=>c[0]==='play'&&c[1]==='answer').length,0);assert.equal(s.recognitions.length,1);
  }
});
test('Quiet recognition can retry; denial stops instead of a permission loop',async()=>{
  const s=setup();s.ready();await tick();s.click('opener');s.welcomeEnd();await tick();
  s.recognitions[0].onerror({error:'no-speech'});s.recognitions[0].onend();s.advance(500);assert.equal(s.recognitions.length,2);
  s.recognitions[1].onerror({error:'not-allowed'});s.recognitions[1].onend();s.advance(1000);assert.equal(s.recognitions.length,2);
});

test('Recognized words remain editable and a failed voice turn has a prepared audible recovery',async()=>{
 const s=setup();s.ready();await tick();s.click('opener');s.welcomeEnd();await tick();
 s.recognitions[0].onresult({results:[[{transcript:'Keep these spoken requirements'}]]});
 assert.equal(s.node('tara-message').value,'Keep these spoken requirements');
 s.requests[0].resolve({ok:false,json:async()=>({error:'Temporarily unavailable'})});await tick();
 const recovery=s.calls.find(c=>c[0]==='play'&&c[1]==='recovery');assert.ok(recovery);
 assert.equal(s.node('tara-message').value,'Keep these spoken requirements');
 recovery[3]();await tick();assert.equal(s.recognitions.length,2);
});
