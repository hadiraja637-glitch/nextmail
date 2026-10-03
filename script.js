let currentVisitorId=localStorage.getItem("nextmail_visitor_token")||"";
let currentEmail=null,expiresAt=null,timerInterval=null;

async function api(path,options={}){
 const headers={...(options.headers||{}),"Content-Type":"application/json"};
 if(window.nextmailSupabase){const s=(await window.nextmailSupabase.auth.getSession()).data.session;if(s)headers.Authorization="Bearer "+s.access_token;}
 if(currentVisitorId)headers["X-NextMail-Visitor"]=currentVisitorId;
 const r=await fetch("/api"+path,{...options,headers});const d=await r.json().catch(()=>({}));
 if(!r.ok)throw new Error(d.detail||"Request failed");return d;
}
function renderTimer(){
 const el=document.getElementById("timer");if(!el||!expiresAt)return;
 const left=Math.max(0,new Date(expiresAt)-Date.now()),s=Math.floor(left/1000);
 el.textContent=String(Math.floor(s/3600)).padStart(2,"0")+":"+String(Math.floor(s%3600/60)).padStart(2,"0")+":"+String(s%60).padStart(2,"0");
 if(left<=0){clearInterval(timerInterval);currentEmail=null;const i=document.getElementById("emailInput");if(i)i.value="Expired — Generate New Email";}
}
function startTimer(x){expiresAt=x;clearInterval(timerInterval);renderTimer();timerInterval=setInterval(renderTimer,1000);}
async function generateEmail(){
 const b=document.querySelector(".new-btn");if(b)b.disabled=true;
 try{const d=await api("/generate-email",{method:"POST",body:JSON.stringify({visitor_token:currentVisitorId})});currentEmail=d.temp_email;currentVisitorId=d.visitor_token||currentVisitorId;localStorage.setItem("nextmail_visitor_token",currentVisitorId);document.getElementById("emailInput").value=currentEmail;startTimer(d.expires_at);loadInbox();}
 catch(e){alert(e.message)}finally{if(b)b.disabled=false}
}
async function copyEmail(){
 if(!currentEmail)return;
 await navigator.clipboard.writeText(currentEmail);
 const b=document.querySelector(".copy-btn");if(b){b.innerText="Copied!";setTimeout(()=>b.innerText="Copy",1500);}
}
async function loadInbox(){
 if(!currentEmail)return;
 try{const d=await api("/inbox/"+encodeURIComponent(currentEmail));startTimer(d.expires_at);window.nextmailInbox=d.messages||[];renderInbox(d.messages||[]);}catch(e){}
}
function renderInbox(messages){
 let box=document.getElementById("inbox");if(!box)return;
 box.innerHTML=messages.length?messages.map(m=>"<article class='inbox-message'><strong>"+escapeHtml(m.subject||"(No subject)")+"</strong><small>"+escapeHtml(m.sender||"Unknown sender")+"</small><p>"+escapeHtml(m.body_text||"")+"</p></article>").join(""):"<p>No messages yet. Incoming mail will appear here.</p>";
}
function escapeHtml(v){return String(v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}

const translations={
 en:{heroTitle:"Instant Temporary Email",heroSub:"Get a disposable email address in seconds. Keep your real inbox safe, private and spam-free.",newBtn:"New Email",activeTimer:"Active for:"},
 es:{heroTitle:"Correo Temporal Instantáneo",heroSub:"Obtenga una dirección de correo electrónico desechable en segundos.",newBtn:"Nuevo Correo",activeTimer:"Activo por:"},
 fr:{heroTitle:"E-mail Temporaire Instantané",heroSub:"Obtenez une adresse e-mail jetable en quelques secondes.",newBtn:"Nouvel E-mail",activeTimer:"Actif pendant :"},
 de:{heroTitle:"Sofortige Wegwerf-E-Mail",heroSub:"Erhalten Sie in Sekundenschnelle eine temporäre E-Mail-Adresse.",newBtn:"Neue E-Mail",activeTimer:"Aktiv für:"},
 ar:{heroTitle:"بريد مؤقت فوري",heroSub:"احصل على عنوان بريد إلكتروني مؤقت في ثوانٍ.",newBtn:"بريد جديد",activeTimer:"نشط لمدة:"},
 zh:{heroTitle:"即时临时电子邮件",heroSub:"几秒钟内获取一次性电子邮件地址。",newBtn:"新邮件",activeTimer:"有效时间："}
};
function changeLanguage(lang){const t=translations[lang];if(!t)return;const a=document.querySelector(".hero-card h1"),b=document.querySelector(".hero-sub"),c=document.querySelector(".new-btn"),d=document.getElementById("timerLabel");if(a)a.innerText=t.heroTitle;if(b)b.innerText=t.heroSub;if(d)d.innerText=t.activeTimer;if(c)c.innerHTML=t.newBtn;}
document.addEventListener("DOMContentLoaded",()=>{const b=document.querySelector(".new-btn");if(b)b.addEventListener("click",generateEmail);generateEmail();});
