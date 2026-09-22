"""Static HTML template for the local Avanza authentication page."""

from string import Template


AUTH_PAGE_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>Connect Avanza</title>
<style nonce="$nonce">
:root {
  --brand:#00c281;
  --brand-dark:#007a58;
  --ink:#10201b;
  --muted:#60706a;
  --line:#dce7e2;
  --surface:#fff;
  --canvas:#f2f7f5;
  --soft:#e9f8f2;
}
* { box-sizing:border-box }
[hidden] { display:none!important }
body {
  margin:0;
  min-height:100vh;
  display:grid;
  place-items:center;
  padding:24px;
  font:15px/1.5 ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
  color:var(--ink);
  background:var(--canvas);
}
.card {
  width:min(100%,520px);
  border:1px solid var(--line);
  border-radius:20px;
  background:var(--surface);
}
main { padding:32px }
.brand { display:flex;align-items:center;margin-bottom:28px }
.wordmark {
  display:flex;
  align-items:flex-end;
  gap:11px;
  font-size:20px;
  font-weight:750;
  letter-spacing:-.03em;
}
.logo { width:30px;height:27px;color:var(--brand) }
h1 {
  margin:0 0 8px;
  font-size:clamp(27px,7vw,36px);
  line-height:1.12;
  letter-spacing:-.04em;
}
.lead { margin:0;color:var(--muted);font-size:16px }
.stage {
  margin:28px 0 22px;
  padding:20px;
  border:1px solid var(--line);
  border-radius:16px;
  background:#fbfdfc;
  text-align:center;
}
#status { margin:0;font-weight:650 }
#helper { margin:5px 0 0;color:var(--muted);font-size:14px }
#qr {
  display:none;
  margin:18px auto 0;
  width:min(100%,290px);
  aspect-ratio:1;
  padding:12px;
  border:1px solid var(--line);
  border-radius:16px;
  background:#fff;
}
#qr.active { display:grid;place-items:center }
#qr svg { display:block;width:100%;height:auto }
.success {
  display:none;
  width:64px;
  height:64px;
  margin:0 auto 14px;
  border-radius:50%;
  place-items:center;
  background:var(--soft);
  color:var(--brand-dark);
  font-size:32px;
}
.success.active { display:grid }
.actions { display:flex;gap:10px }
button {
  min-height:48px;
  border-radius:12px;
  padding:0 18px;
  border:0;
  font:inherit;
  font-weight:700;
  cursor:pointer;
}
button:focus-visible {
  outline:3px solid rgba(0,194,129,.28);
  outline-offset:2px;
}
#start { flex:1;color:#fff;background:var(--brand-dark) }
#start:hover { background:#006548 }
#cancel { color:var(--ink);background:#eef3f1 }
button:disabled { cursor:wait;opacity:.58 }
.notes {
  margin:22px 0 0;
  padding-top:20px;
  border-top:1px solid var(--line);
  color:var(--muted);
  font-size:13px;
}
.notes p { margin:0 }
.notes p+p { margin-top:10px }
@media(max-width:480px) {
  body { padding:12px }
  main { padding:24px 20px }
  .card { border-radius:16px }
  .actions { flex-direction:column }
  #cancel { order:2 }
}
@media(prefers-color-scheme:dark) {
  :root {
    --ink:#eef8f4;
    --muted:#9aada5;
    --line:#2c3d36;
    --surface:#13211c;
    --canvas:#09110e;
    --soft:#153c30;
  }
  .stage { background:#101d18 }
  #qr { background:#fff }
  #cancel { background:#263731;color:var(--ink) }
}
</style>
</head>
<body>
<article class="card">
<main>
<header class="brand">
  <div class="wordmark" aria-label="Avanza MCP">
    <svg class="logo" viewBox="0 0 32 28" aria-hidden="true">
      <rect x="1" y="17" width="6" height="10" fill="currentColor"/>
      <rect x="9" y="13" width="6" height="14" fill="currentColor"/>
      <rect x="17" y="8" width="6" height="19" fill="currentColor"/>
      <rect x="25" y="1" width="6" height="26" fill="currentColor"/>
    </svg>
    <span>Avanza MCP</span>
  </div>
</header>
<section>
  <h1 id="title">$title</h1>
  <p class="lead" id="lead">$lead</p>
</section>
<section class="stage" aria-live="polite">
  <div id="success" class="success" aria-hidden="true">✓</div>
  <p id="status" role="status">$status</p>
  <p id="helper">$helper</p>
  <div id="qr"></div>
</section>
<div id="actions" class="actions">
  <button id="start" type="button">$primary</button>
  <button id="cancel" type="button">$secondary</button>
</div>
<aside class="notes">
  <p>No Avanza password is requested. Account tool results may be sent to your configured model provider and saved in chat history.</p>
  <p>Avanza MCP is an independent project. It is not affiliated with, endorsed by, or supported by Avanza Bank AB. Use it at your own risk; its maintainers accept no responsibility for losses or damages.</p>
</aside>
</main>
</article>
<script nonce="$nonce">
const csrf=$csrf;
const base=$path;
const disconnecting=$disconnect_mode;
const status=document.getElementById('status');
const helper=document.getElementById('helper');
const qr=document.getElementById('qr');
const title=document.getElementById('title');
const lead=document.getElementById('lead');
const actions=document.getElementById('actions');
const start=document.getElementById('start');
const success=document.getElementById('success');
const terminal=['connected','denied','timed_out','error','disconnected'];

async function call(suffix,method='GET') {
  const response=await fetch(base+suffix,{
    method,
    headers:method==='POST'?{'X-CSRF-Token':csrf}:{}
  });
  if(!response.ok) throw new Error('request failed');
  return response.json();
}

function render(state) {
  status.textContent=state.message;
  qr.innerHTML=state.qr_svg||'';
  qr.classList.toggle('active',!!state.qr_svg);
  start.disabled=['starting','scanning'].includes(state.state);
  start.hidden=['starting','scanning'].includes(state.state);
  if(state.state==='scanning') {
    helper.textContent='Open the BankID app on your phone and scan this QR code.';
  } else if(!disconnecting) {
    helper.textContent='Approve access to continue with BankID.';
  }
  if(state.state==='connected') {
    title.textContent=disconnecting?'Still connected':"You're connected";
    lead.textContent='Avanza account access is ready in your MCP client.';
    status.textContent=disconnecting?'Disconnection cancelled':'Authentication complete';
    helper.textContent='You can now close this window and return to your MCP client.';
    success.classList.add('active');
    actions.hidden=true;
  } else if(['denied','timed_out','error','disconnected'].includes(state.state)) {
    title.textContent=state.state==='disconnected'
      ?(disconnecting?'Disconnected':'Connection cancelled')
      :'Could not connect';
    lead.textContent=disconnecting
      ?'The saved Avanza session was removed.'
      :lead.textContent;
    helper.textContent='You can close this window.';
    actions.hidden=true;
  }
}

async function refresh() {
  try {
    const state=await call('/status');
    render(state);
    if(terminal.includes(state.state)) clearInterval(timer);
  } catch {
    status.textContent='The local authentication page is no longer available.';
    helper.textContent='You can close this window.';
    actions.hidden=true;
  }
}

start.onclick=async()=>{
  start.disabled=true;
  start.hidden=true;
  status.textContent=disconnecting?'Disconnecting…':'Starting BankID…';
  helper.textContent='Please wait.';
  try {
    render(await call(disconnecting?'/disconnect':'/start','POST'));
    if(!disconnecting) await refresh();
    else clearInterval(timer);
  } catch {
    status.textContent=disconnecting?'Could not disconnect.':'Could not start BankID.';
    helper.textContent='Try again or close this window.';
    start.textContent='Try again';
    start.disabled=false;
    start.hidden=false;
  }
};

document.getElementById('cancel').onclick=async()=>{
  render(await call(disconnecting?'/keep':'/cancel','POST'));
  clearInterval(timer);
};

const timer=setInterval(refresh,1500);
refresh();
</script>
</body>
</html>"""
)
