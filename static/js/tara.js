/* Tara is additive: existing forms, payment verification and apps remain authoritative. */
(() => {
  'use strict';
  const app = document.getElementById('tara-app');
  if (!app) return;
  const $ = id => document.getElementById('tara-' + id);
  const dialog = document.getElementById('tara-dialog');
  const mode = app.dataset.mode;
  let state, busy = false, voiceMode = false, audio, recognition, recorder, stream, recordTimer, meterTimer, context;
  let reviewKind = 'help', reviewToken = '', lastReply = 'welcome';
  let voiceEpoch=0;
  let audioUrl='';
  const csrf = document.querySelector('meta[name="csrf-token"]').content;
  const status = (text, error=false) => { $('status').textContent=text; $('status').classList.toggle('tara-error',error); };
  function stopTracks() {
    if(stream) stream.getTracks().forEach(t=>t.stop());
    stream=null; clearTimeout(recordTimer); clearInterval(meterTimer);
    if(context) {context.close().catch(()=>{}); context=null;}
  }
  function stopListening() {
    if(recognition) { recognition.abort(); recognition=null; }
    if(recorder && recorder.state==='recording') { recorder.onstop=null; recorder.stop(); }
    stopTracks();
  }
  function stopVoice() {
    voiceEpoch++;
    voiceMode=false;
    stopListening();
    if(audio) { audio.pause(); audio=null; }
    if(audioUrl){URL.revokeObjectURL(audioUrl);audioUrl='';}
    $('voice').textContent='Start voice conversation';
    status('Voice stopped. You can keep typing.');
  }
  function setBusy(value) {
    busy=value; $('send').disabled=value; $('prepare').disabled=value;
    ['order','help','reset'].forEach(id=>$(id).disabled=value);
    document.querySelectorAll('[data-tara-prompt]').forEach(b=>b.disabled=value);
  }
  async function api(path, data) {
    const response = await fetch('/api/tara/'+path,{method:'POST',credentials:'same-origin',
      headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify({...data,mode})});
    const result = await response.json();
    if(!response.ok) throw new Error(result.error || 'Please try again.');
    return result;
  }
  function render(result, announce=false) {
    state=result;
    if($('sandbox-readiness')) $('sandbox-readiness').textContent=result.sandbox_ready?'PayPal sandbox is connected. Use a test buyer account for checkout.':'PayPal sandbox checkout is awaiting configuration. You can explore the conversation and draft review; payment is not yet available in this demo.';
    const history=$('history'); history.replaceChildren();
    result.history.forEach(message=>{
      const box=document.createElement('div');box.className='tara-message '+(message.role==='user'?'user':'assistant');
      const label=document.createElement('strong');label.textContent=message.role==='user'?'You':'Tara';
      const p=document.createElement('p');p.textContent=message.text;
      box.append(label,p);history.append(box);
      if(message.role==='assistant') lastReply=message.id;
    });
    history.scrollTop=history.scrollHeight;
    $('service').replaceChildren(); $('service').hidden=!result.item;
    if(result.item) {
      const item=result.item;
      const title=document.createElement('h3');title.id='tara-service-title';title.textContent=item.name;
      const price=document.createElement('p');price.className='tara-price';price.textContent=item.price_label;
      const summary=document.createElement('p');summary.textContent=item.summary;
      const list=document.createElement('ul');item.includes.forEach(line=>{const li=document.createElement('li');li.textContent=line;list.append(li);});
      const timing=document.createElement('p');timing.textContent=item.turnaround;
      $('service').append(title,price,summary,list,timing);
    }
    $('order').hidden=!(result.item && result.item.cta==='buy');
    $('resources').replaceChildren();
    (result.resources||[]).forEach(resource=>{const link=document.createElement('a');link.href=resource.url;link.textContent=resource.label;$('resources').append(link);});
    $('review').hidden=true; $('sandbox-confirm').hidden=true;
    if(announce && !voiceMode) $('announcement').textContent=result.history[result.history.length-1].text;
  }
  async function speak(id, resume=false) {
    const epoch=++voiceEpoch;
    if(audio) audio.pause();
    if(audioUrl){URL.revokeObjectURL(audioUrl);audioUrl='';}
    status('Preparing Tara’s voice…');
    try {
      const response=await fetch('/api/tara/voice',{method:'POST',credentials:'same-origin',
        headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:JSON.stringify({mode,message_id:id})});
      if(!response.ok) {const e=await response.json();throw new Error(e.error);}
      if(epoch!==voiceEpoch)return;
      const url=URL.createObjectURL(await response.blob()); audioUrl=url;audio=new Audio(url);
      audio.onended=()=>{URL.revokeObjectURL(url);audio=null;status('Ready.');if(epoch===voiceEpoch&&resume&&voiceMode) listen();};
      audio.onerror=()=>{URL.revokeObjectURL(url);status('Audio could not play. The reply is available as text.',true);};
      await audio.play(); status('Tara is speaking. Use Stop voice to interrupt.');
    }catch(e){status(e.message || 'Voice is unavailable. You can keep typing.',true);}
  }
  async function send(text) {
    if(busy || !text.trim()) return;
    stopListening();
    if(audio) audio.pause();
    setBusy(true);status('Tara is checking the published information…');
    try {
      const result=await api('chat',{message:text.trim(),page:location.pathname}); render(result,true);$('message').value='';status('Ready.');
      if(voiceMode) await speak(lastReply,true);
    } catch(e) {status(e.message,true);}
    finally {setBusy(false);}
  }
  async function transcribe(blob) {
    setBusy(true);status('Listening complete. Preparing your words…');
    try {
      const form=new FormData();form.append('audio',blob,'voice.webm');
      const response=await fetch('/api/tara/transcribe',{method:'POST',headers:{'X-CSRF-Token':csrf},body:form});
      const result=await response.json();if(!response.ok)throw new Error(result.error);
      // Keep the transcript visible and editable as well as in the conversation.
      $('message').value=result.transcript;setBusy(false);await send(result.transcript);
    }catch(e){status(e.message,true);setBusy(false);}
  }
  async function listen() {
    if(!voiceMode || busy || document.hidden || (dialog && !dialog.open)) return;
    if(audio) {audio.pause();audio=null;}
    const Recognition=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(Recognition) {
      recognition=new Recognition();recognition.lang='en-US';recognition.interimResults=false;recognition.continuous=false;
      recognition.onresult=e=>{const text=e.results[0][0].transcript;recognition=null;send(text);};
      recognition.onerror=e=>{if(e.error!=='aborted')status('Microphone recognition is unavailable. Try again or type your message.',true);};
      recognition.onend=()=>{recognition=null;$('voice').textContent='Speak again';};
      try {recognition.start();status('Listening. Speak naturally; Tara will respond when you finish.');$('voice').textContent='Listening…';}
      catch(e){status('Please allow microphone access or type instead.',true);}
      return;
    }
    if(!navigator.mediaDevices || !window.MediaRecorder){status('Voice recording is unavailable in this browser. Please type instead.',true);return;}
    try {
      stream=await navigator.mediaDevices.getUserMedia({audio:true});
      const mime=['audio/webm;codecs=opus','audio/mp4','audio/ogg;codecs=opus'].find(m=>MediaRecorder.isTypeSupported(m));
      recorder=new MediaRecorder(stream,mime?{mimeType:mime}:{});const chunks=[];
      recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
      recorder.onstop=()=>{const blob=new Blob(chunks,{type:recorder.mimeType});stopTracks();$('voice').textContent='Speak again';if(voiceMode)transcribe(blob);};
      recorder.start();status('Listening. Select Finish speaking when ready; recording stops after 30 seconds.');$('voice').textContent='Finish speaking';
      recordTimer=setTimeout(()=>{if(recorder.state==='recording')recorder.stop();},30000);
      // End a voice turn after speech followed by a short silence; no recording
      // is kept in the browser after it has been sent for transcription.
      const AudioCtx=window.AudioContext||window.webkitAudioContext;
      if(AudioCtx){context=new AudioCtx();const source=context.createMediaStreamSource(stream),analyser=context.createAnalyser();source.connect(analyser);analyser.fftSize=512;const samples=new Uint8Array(512);let heard=false,lastSound=Date.now(),started=Date.now();meterTimer=setInterval(()=>{analyser.getByteTimeDomainData(samples);const energy=samples.reduce((s,v)=>s+(v-128)**2,0)/samples.length;if(energy>35){heard=true;lastSound=Date.now();}if(heard&&Date.now()-lastSound>1300&&Date.now()-started>1800&&recorder.state==='recording')recorder.stop();},150);}
    }catch(e){stopTracks();status('Microphone access was not granted. You can use the message box instead.',true);}
  }
  $('voice').addEventListener('click',()=>{
    if(recorder&&recorder.state==='recording'){recorder.stop();return;}
    if(recognition){recognition.stop();return;}
    voiceMode=true;if(state&&state.history.length===1)speak('welcome',true);else listen();
  });
  $('stop').addEventListener('click',stopVoice);
  $('repeat').addEventListener('click',()=>{stopListening();speak(lastReply,false);});
  $('chat-form').addEventListener('submit',e=>{e.preventDefault();send($('message').value);});
  document.querySelectorAll('[data-tara-prompt]').forEach(b=>b.addEventListener('click',()=>send(b.dataset.taraPrompt)));
  $('reset').addEventListener('click',async()=>{stopVoice();try{render(await api('reset',{}));status('A new conversation is ready.');}catch(e){status(e.message,true);}});
  function review(kind) {
    const wasVoice=voiceMode;stopVoice(); reviewKind=kind;reviewToken='';$('sandbox-confirm').hidden=true;$('review-form').hidden=false;
    $('review').hidden=false;
    $('review-title').textContent=kind==='order'?'Review your service order':'Prepare a customer-service request';
    const item=state.item;
    $('review-description').textContent=kind==='order'?item.name+' — '+item.price_label+'. '+item.turnaround:'The team will receive the details you choose to submit. Tara has not sent anything.';
    ['name','email','organization','target_url','notes'].forEach(k=>$(''+k).value=state.fields[k]||'');
    if(kind==='help') $('notes').value=state.fields.message||state.fields.notes||state.history.filter(m=>m.role==='user').map(m=>m.text).join('\n');
    $('name').required=kind==='help';$('notes').required=kind==='help';
    $('target-wrap').hidden=!(kind==='order'&&item.needs_target_url);$('target_url').required=kind==='order'&&!!item.needs_target_url;
    $('prepare').textContent=mode==='sandbox'&&kind==='order'?'Review sandbox payment':'Continue to the completed form';
    $('review-title').focus();
    if(wasVoice) readReview();
  }
  async function readReview(){
    try{const fields=Object.fromEntries(new FormData($('review-form')));const result=await api('review-summary',{kind:reviewKind,sku:state.sku,fields});await speak(result.message_id,false);}
    catch(e){status(e.message,true);}
  }
  $('read-review').addEventListener('click',readReview);
  $('order').addEventListener('click',()=>review('order'));$('help').addEventListener('click',()=>review('help'));
  $('review-form').addEventListener('submit',async e=>{
    e.preventDefault();const fields=Object.fromEntries(new FormData(e.target));fields.message=fields.notes;
    setBusy(true);status('Preparing your reviewed details…');
    try {
      const result=await api('prepare',{kind:reviewKind,sku:state.sku,fields});
      if(result.kind==='sandbox'){
        reviewToken=result.review_token;$('sandbox-summary').textContent=result.item.name+' — '+result.item.price_label+' USD (test money). '+result.message;
        $('sandbox-confirm').hidden=false;$('review-form').hidden=true;$('paypal').disabled=!state.sandbox_ready;if(state.sandbox_ready)$('paypal').focus();status(state.sandbox_ready?'Please review and approve the sandbox handoff.':'The draft is ready. PayPal sandbox configuration is still needed before checkout.');
      }else{
        sessionStorage.setItem('tara_handoff',JSON.stringify({destination:result.destination,form:result.form,created:Date.now()}));
        location.assign(result.destination);
      }
    }catch(e){status(e.message,true);}finally{setBusy(false);}
  });
  $('paypal').addEventListener('click',async()=>{
    $('paypal').disabled=true;status('Opening secure PayPal sandbox checkout…');
    try{const result=await api('checkout',{review_token:reviewToken,confirmed:true});const dest=new URL(result.approval_url);if(dest.hostname!=='www.sandbox.paypal.com')throw new Error('Invalid checkout destination.');location.assign(dest.href);}
    catch(e){status(e.message,true);$('paypal').disabled=false;}
  });
  document.querySelectorAll('[data-tara-open]').forEach(link=>link.addEventListener('click',e=>{
    if(dialog){e.preventDefault();dialog.showModal();$('message').focus();}
  }));
  const close=document.getElementById('tara-close');if(close)close.addEventListener('click',()=>dialog.close());
  if(dialog)dialog.addEventListener('close',stopVoice);
  document.addEventListener('visibilitychange',()=>{if(document.hidden)stopVoice();});
  window.addEventListener('pagehide',stopVoice);
  // Only fill explicitly allowlisted fields on the expected existing form.
  // The visitor still reviews and activates that form's own submit button.
  try{
    const raw=sessionStorage.getItem('tara_handoff');
    if(raw){const handoff=JSON.parse(raw);if(handoff.destination===location.pathname&&Date.now()-handoff.created<900000){
      const form=document.querySelector(location.pathname==='/contact'?'form[action="/contact"]':'#buy-form');
      if(form){const allowed=['name','email','organization','target_url','notes','message','interest'];for(const [k,v] of Object.entries(handoff.form)){if(allowed.includes(k)){const input=form.elements.namedItem(k);if(input)input.value=v;}}
        const note=document.createElement('p');note.className='tara-handoff';note.tabIndex=-1;note.setAttribute('role','status');note.textContent='Tara has filled in your details. Please review the form below, make any corrections, and use its submit button when ready. Nothing has been submitted yet.';form.before(note);note.focus();sessionStorage.removeItem('tara_handoff');
      }
    }else if(Date.now()-handoff.created>=900000)sessionStorage.removeItem('tara_handoff');}
  }catch(e){/* Storage unavailable: regular forms remain usable. */}
  fetch('/api/tara/session?mode='+mode,{credentials:'same-origin',cache:'no-store'}).then(r=>r.json()).then(r=>render(r)).catch(()=>status('Please reload Tara or use the regular forms.',true));
})();
