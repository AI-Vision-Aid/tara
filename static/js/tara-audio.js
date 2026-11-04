/* Incremental speech playback. No microphone access; all audio stays in memory. */
(() => {
  'use strict';
  class TaraAudio {
    constructor(csrf, status) {
      this.csrf=csrf; this.status=status; this.epoch=0; this.sources=new Set();
    }
    setWelcome(audio) {
      this.welcomeAudio=audio;
      if(audio){audio.preload='auto';audio.load();}
    }
    setThinking(audio) {
      this.thinkingAudio=audio;
      if(audio){audio.preload='auto';audio.load();}
    }
    async playWelcome(onEnd) {
      return this.playPrepared(this.welcomeAudio,onEnd,'welcome');
    }
    setRecovery(audio) {this.recoveryAudio=audio;if(audio){audio.preload='auto';audio.load();}}
    async playThinking() {
      return this.playPrepared(this.thinkingAudio,null,'thinking');
    }
    async playPrepared(audio,onEnd,kind) {
      this.cancel(); const epoch=this.epoch;
      if(!audio)return false;
      const active=()=>epoch===this.epoch;
      this.audio=audio;audio.currentTime=0;
      audio.onended=()=>{if(active()){this.audio=null;this.status(kind==='thinking'?'Tara is checking the published information…':'Ready. You can speak or type.');if(onEnd)onEnd();}};
      audio.onerror=()=>{if(active()){this.cancel();this.status(kind==='thinking'?'Tara is checking the published information…':'The welcome is available as text. You can continue with voice or typing.',kind!=='thinking');}};
      try {
        // Start in the original click gesture. No session, synthesis or POST wait.
        const playback=audio.play();
        if(playback)await playback;
        if(active()){this.status(kind==='thinking'?'Tara is checking the published information…':kind==='recovery'?'Tara is explaining how to continue.':'Tara is welcoming you. Listening starts when the greeting finishes.');return true;}
        return false;
      } catch(error) {
        if(active()){this.cancel();this.status(kind==='thinking'?'Tara is checking the published information…':'You can continue with voice or type your message.',kind!=='thinking');}
        return false;
      }
    }
    async prime() {
      const AudioCtx=window.AudioContext||window.webkitAudioContext;
      if(!AudioCtx) return false;
      if(!this.context || this.context.state==='closed') this.context=new AudioCtx();
      if(this.context.state==='suspended') await this.context.resume();
      return this.context.state==='running';
    }
    cancel() {
      this.epoch++;
      if(this.controller) this.controller.abort();
      this.controller=null;
      for(const source of this.sources) {source.onended=null;try{source.stop();}catch(e){} source.disconnect();}
      this.sources.clear();
      if(this.audio) {this.audio.onended=null;this.audio.onerror=null;this.audio.pause();this.audio=null;}
      if(this.url) {URL.revokeObjectURL(this.url);this.url='';}
      this.nextTime=0;
    }
    async play(id, mode, onEnd) {
      if(id==='recovery' && this.recoveryAudio)return this.playPrepared(this.recoveryAudio,onEnd,'recovery');
      if(id==='welcome' && this.welcomeAudio)return this.playWelcome(onEnd);
      this.cancel(); const epoch=this.epoch;
      const controller=new AbortController();this.controller=controller;
      const active=()=>epoch===this.epoch && !controller.signal.aborted;
      const request=(path)=>fetch('/api/tara/'+path,{method:'POST',credentials:'same-origin',signal:controller.signal,
        headers:{'Content-Type':'application/json','X-CSRF-Token':this.csrf},body:JSON.stringify({mode,message_id:id})});
      let finished=false, ended=false;
      const finish=()=>{
        if(active() && finished && !this.sources.size && !ended){ended=true;this.status('Ready.');if(onEnd)setTimeout(()=>{if(active())onEnd();},0);}
      };
      this.status('Preparing Tara’s voice…');
      try {
        const streaming=id!=='welcome' && await this.prime();
        if(!active())return;
        const response=await request(streaming?'voice-stream':'voice');
        if(!response.ok){const error=await response.json();throw new Error(error.error||'Voice is unavailable.');}
        if(!active())return;
        if(!streaming){
          const blob=await response.blob();if(!active())return;
          this.url=URL.createObjectURL(blob);this.audio=new Audio(this.url);
          this.audio.onended=()=>{if(!active())return;URL.revokeObjectURL(this.url);this.url='';this.audio=null;finished=true;finish();};
          this.audio.onerror=()=>{if(active()){this.cancel();this.status('Audio could not play. The reply is available as text.',true);}};
          await this.audio.play();if(active())this.status('Tara is speaking. Use Stop voice to interrupt.');
          return;
        }
        if(!response.body)throw new Error('Streaming audio is unavailable in this browser. You can keep typing.');
        const reader=response.body.getReader(), decoder=new TextDecoder();let pending='', rate=0, done=false;
        const consume=(line)=>{
          if(!line.trim()||!active())return;
          const event=JSON.parse(line);
          if(event.error)throw new Error(event.error);
          if(event.sample_rate){if(event.sample_rate!==24000)throw new Error('Unsupported audio format.');rate=event.sample_rate;}
          if(event.audio){
            if(!rate || done)throw new Error('Invalid audio stream.');
            const bytes=Uint8Array.from(atob(event.audio),c=>c.charCodeAt(0));
            if(!bytes.length || bytes.length%2)throw new Error('Invalid audio stream.');
            const view=new DataView(bytes.buffer), buffer=this.context.createBuffer(1,bytes.length/2,rate), samples=buffer.getChannelData(0);
            for(let i=0;i<samples.length;i++)samples[i]=view.getInt16(i*2,true)/32768;
            const source=this.context.createBufferSource();source.buffer=buffer;source.connect(this.context.destination);
            this.sources.add(source);source.onended=()=>{source.disconnect();this.sources.delete(source);finish();};
            this.nextTime=Math.max(this.nextTime,this.context.currentTime+0.06);source.start(this.nextTime);this.nextTime+=buffer.duration;
            if(this.nextTime-this.context.currentTime>180)throw new Error('Audio response is too long.');
            if(!this.spokenEpoch || this.spokenEpoch!==epoch){this.spokenEpoch=epoch;this.status('Tara is speaking. Use Stop voice to interrupt.');}
          }
          if(event.done)done=true;
        };
        try {
          while(active()){
            const packet=await reader.read();if(packet.done)break;
            pending+=decoder.decode(packet.value,{stream:true});
            let index;while((index=pending.indexOf('\n'))>=0){consume(pending.slice(0,index));pending=pending.slice(index+1);}
            if(pending.length>12*1024*1024)throw new Error('Invalid audio stream.');
          }
          if(!active())return;
          pending+=decoder.decode();if(pending.trim())consume(pending);
          if(!done)throw new Error('Voice was interrupted. The reply is available as text.');
          finished=true;finish();
        } finally {await reader.cancel().catch(()=>{});reader.releaseLock();}
      }catch(error){
        if(!active())return;
        this.cancel();this.status(error.message||'Voice is unavailable. You can keep typing.',true);
      }
    }
  }
  window.TaraAudio=TaraAudio;
})();
