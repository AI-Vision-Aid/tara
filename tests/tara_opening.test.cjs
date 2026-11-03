/* Real opening-handler regression checks with session loading held pending. */
const {test}=require('node:test'), assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const tick=()=>new Promise(r=>setImmediate(r));
function setup(){
  const nodes=new Map(),calls=[],events=new Map();let resolveSession,microphones=0;
  function node(id){
    if(!nodes.has(id))nodes.set(id,{id,dataset:{mode:'sandbox'},handlers:{},classList:{toggle(){}},textContent:'',hidden:false,
      addEventListener(name,fn){this.handlers[name]=fn;},focus(){},replaceChildren(){},append(){},
      showModal(){this.open=true;},close(){this.open=false;this.handlers.close?.();}});
    return nodes.get(id);
  }
  const dialog=node('tara-dialog'),opener=node('opener');
  class Speech {
    setWelcome(audio){calls.push(['prepare',audio.id]);}
    play(id,mode,done){calls.push(['play',id,mode]);return Promise.resolve();}
    cancel(){calls.push(['cancel']);}
    prime(){return Promise.resolve(true);}
  }
  const document={hidden:false,getElementById:node,querySelector:selector=>selector.startsWith('meta')?{content:'test'}:null,
    querySelectorAll:selector=>selector==='[data-tara-open]'?[opener]:[],
    addEventListener:(name,fn)=>events.set(name,fn),createElement:()=>node('created-'+nodes.size)};
  const window={TaraAudio:Speech,addEventListener(){},MediaRecorder:null};
  const context={document,window,location:{pathname:'/'},navigator:{mediaDevices:{getUserMedia(){microphones++;}}},
    sessionStorage:{getItem(){return null;}},fetch:()=>new Promise(r=>{resolveSession=r;}),setTimeout,clearTimeout,clearInterval};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../static/js/tara.js'),'utf8'),context);
  return{dialog,calls,node,microphones:()=>microphones,click:target=>node(target).handlers.click?.({preventDefault(){}}),
    ready(){resolveSession({json:async()=>({history:[{role:'assistant',text:'Welcome',id:'welcome'}],resources:[],fields:{},sandbox_ready:true})});}};
}
test('Opening Tara speaks its welcome immediately while session initialization is pending, without starting the microphone',async()=>{
  const s=setup();s.click('opener');
  assert.equal(s.dialog.open,true);assert.deepEqual(s.calls.filter(x=>x[0]==='play'),[['play','welcome','sandbox']]);
  assert.equal(s.microphones(),0);s.ready();await tick();assert.equal(s.calls.filter(x=>x[0]==='play').length,1);
});
test('Closing before session initialization stops speech and never starts another greeting when initialization finishes',async()=>{
  const s=setup();s.click('opener');s.click('tara-close');
  assert.equal(s.dialog.open,false);assert.ok(s.calls.some(x=>x[0]==='cancel'));
  s.ready();await tick();assert.equal(s.calls.filter(x=>x[0]==='play').length,1);assert.equal(s.microphones(),0);
});
test('Reopening the same page does not repeatedly interrupt the conversation with the welcome',()=>{
  const s=setup();s.click('opener');s.click('tara-close');s.click('opener');
  assert.equal(s.calls.filter(x=>x[0]==='play').length,1);assert.equal(s.microphones(),0);
});
