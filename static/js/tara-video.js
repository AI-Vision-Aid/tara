/* User-initiated video only; no auto-play or conversation side effects. */
document.querySelectorAll('[data-tara-film]').forEach(button=>button.addEventListener('click',()=>{
  const target=document.getElementById(button.getAttribute('aria-controls'));
  const open=button.getAttribute('aria-expanded')==='true';
  if(open){target.replaceChildren();target.hidden=true;button.textContent='Watch the TARA demonstration';}
  else{const frame=document.createElement('iframe');frame.src='https://www.youtube-nocookie.com/embed/7dBsvmOW2ag';frame.title='TARA: voice-guided discovery, reviewed request and PayPal test checkout';frame.allowFullscreen=true;target.append(frame);target.hidden=false;button.textContent='Close the TARA demonstration';}
  button.setAttribute('aria-expanded',String(!open));
}));
