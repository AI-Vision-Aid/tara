/* Offline playback lifecycle checks; no browser, microphone or paid API needed. */
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'), vm=require('node:vm'), path=require('node:path');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
function setup(){
  let body, signal;const sources=[], statuses=[];let resumed=0;
  class Context {
    constructor(){this.state='running';this.currentTime=0;this.destination={};}
    async resume(){this.state='running';}
    createBuffer(channels,length,rate){const samples=new Float32Array(length);return{duration:length/rate,getChannelData:()=>samples};}
    createBufferSource(){const source={connect(){},disconnect(){},start(time){this.startTime=time;},stop(){this.stopped=true;},end(){this.onended?.();}};sources.push(source);return source;}
  }
  const window={AudioContext:Context};
  const sandbox={window,URL,AbortController,TextDecoder,Uint8Array,DataView,Float32Array,Set,atob,setTimeout,
    fetch:async(url,options)=>{signal=options.signal;return{ok:true,body:new ReadableStream({start(controller){body=controller;signal.addEventListener('abort',()=>{try{controller.close();}catch(e){}});}})};}};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../static/js/tara-audio.js'),'utf8'),sandbox);
  const audio=new window.TaraAudio('test',(text)=>statuses.push(text));
  const write=text=>body.enqueue(new TextEncoder().encode(text));
  const chunk=Buffer.from([0,128,0,0,255,127]).toString('base64');
  return{audio,sources,statuses,write,chunk,end:()=>body.close(),signal:()=>signal,onEnd:()=>{resumed++;},resumed:()=>resumed};
}
test('PCM begins before full response; little-endian samples and sequential scheduling; resume waits for final sound',async()=>{
  const s=setup();const playing=s.audio.play('reply','sandbox',s.onEnd);await tick();
  s.write('{"sample_rate":24000}\n{"audio":"'+s.chunk+'"}\n');await tick();
  assert.equal(s.sources.length,1);assert.equal(s.sources[0].buffer.getChannelData(0)[0],-1);
  assert.equal(s.resumed(),0);
  s.write('{"audio":"'+s.chunk+'"}\n{"done":true}\n');s.end();await playing;
  assert.equal(s.sources.length,2);assert.ok(s.sources[1].startTime>=s.sources[0].startTime+s.sources[0].buffer.duration);
  s.sources[0].end();assert.equal(s.resumed(),0);s.sources[1].end();await new Promise(r=>setTimeout(r,5));
  assert.equal(s.resumed(),1);
});
test('Stop cancels the request and all queued sound; late response never resumes listening',async()=>{
  const s=setup();const playing=s.audio.play('reply','sandbox',s.onEnd);await tick();
  s.write('{"sample_rate":24000}\n{"audio":"'+s.chunk+'"}\n');await tick();s.audio.cancel();await playing;
  assert.ok(s.signal().aborted);assert.ok(s.sources.every(x=>x.stopped));assert.equal(s.audio.sources.size,0);
  s.sources[0].end();await tick();assert.equal(s.resumed(),0);
});
test('Network truncation stops queued audio and reports text fallback',async()=>{
  const s=setup();const playing=s.audio.play('reply','sandbox',s.onEnd);await tick();
  const line='{"sample_rate":24000}\n{"audio":"'+s.chunk+'"}\n';s.write(line.slice(0,27));s.write(line.slice(27));s.end();await playing;
  assert.ok(s.sources.every(x=>x.stopped));assert.equal(s.resumed(),0);assert.match(s.statuses.at(-1),/interrupted/);
});
