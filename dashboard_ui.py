DASHBOARD_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Australigo · Teacher Inbox</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:#222541;background:#f5f6fa}
*{box-sizing:border-box}body{margin:0}button,input{font:inherit}button{cursor:pointer}
button:focus-visible,input:focus-visible{outline:3px solid #9a86fa;outline-offset:2px}
.layout{min-height:100vh;display:grid;grid-template-columns:220px 335px minmax(0,1fr)}
.side{background:#191b35;color:#b7b9d5;padding:30px 18px;display:flex;flex-direction:column;gap:26px}
.brand{display:flex;gap:12px;align-items:center;color:white;font-weight:800;font-size:21px;letter-spacing:-1px}
.brand b{width:36px;height:36px;background:linear-gradient(135deg,#aa94ff,#735de3);border-radius:12px;display:grid;place-items:center}
.side .small{font-size:11px;color:#8386a8;letter-spacing:1.5px;text-transform:uppercase;margin:18px 10px 8px}
.nav{padding:12px 14px;background:#313052;border-radius:11px;color:#fff;font-size:13px;font-weight:650}
.sidebottom{margin-top:auto;padding:16px;border:1px solid #343654;background:#242642;border-radius:15px;font-size:12px;line-height:1.7}
.sidebottom strong{color:white}.dot{color:#4ddaaf}
.inbox{background:white;border-right:1px solid #ececf4;display:flex;flex-direction:column;min-height:100vh;min-width:0}
.inbox-head{padding:32px 23px 17px}.overline{font-size:10px;color:#826ada;font-weight:800;text-transform:uppercase;letter-spacing:1.6px}
h1{font-size:29px;letter-spacing:-1px;margin:8px 0 2px}.muted{color:#8d93a7;font-size:12px;line-height:1.6}
.search{display:block;width:100%;margin:22px 0 14px;padding:12px 14px;background:#f8f8fc;border:1px solid #eaebf3;border-radius:11px;font-size:12px}
.filters{display:flex;gap:7px}.filter{background:#f3f4f9;border:0;border-radius:100px;padding:9px 13px;color:#7d8397;font-size:11px;font-weight:700}
.filter.on{background:#efebff;color:#7659d8}.countline{padding:14px 23px;border-bottom:1px solid #f0f0f5;font-size:11px;color:#9298a8}
#conversations{overflow:auto;flex:1}.conversation{width:100%;border:0;border-bottom:1px solid #f0f1f6;background:white;padding:19px 22px;display:flex;gap:12px;text-align:left}
.conversation:hover{background:#fbfaff}.conversation.active{background:#f6f3ff;border-left:3px solid #7e62e5;padding-left:19px}
.avatar{background:#e9e4fc;color:#6650bb;width:43px;height:43px;min-width:43px;border-radius:15px;display:grid;place-items:center;font-weight:800;font-size:13px}
.conversation:nth-child(2n) .avatar{background:#e0f5ee;color:#368d75}.cbody{flex:1;min-width:0}
.cname{font-size:13px;font-weight:800;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.ctime{font-size:10px;color:#a2a6b4;white-space:nowrap}
.cmeta{color:#8e92a2;font-size:10px;margin:5px 0}.preview{color:#9296a6;font-size:11px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:210px}
.crow{display:flex;align-items:center;justify-content:space-between;gap:6px}.bubblecount{background:#8468e9;color:white;border-radius:10px;padding:2px 7px;font-size:10px}
.work{display:flex;flex-direction:column;min-width:0;height:100vh}.top{background:white;border-bottom:1px solid #ececf4;padding:20px 30px;display:flex;align-items:center;justify-content:space-between;gap:10px}
.crumb{font-size:12px;color:#8d91a5}.crumb strong{color:#30334f}.badges{display:flex;gap:8px;flex-wrap:wrap}
.badge{background:#fff0d7;color:#986729;padding:8px 11px;border-radius:24px;font-weight:800;font-size:10px}.live{background:#e8f9ef;color:#277c5c}
.content{padding:25px 30px 28px;display:flex;flex-direction:column;min-height:0;flex:1;gap:20px}
.heading h2{font-size:25px;margin:0 0 5px;letter-spacing:-.9px}.stats{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.stat{background:white;border:1px solid #ebedf4;border-radius:15px;padding:16px 18px}.stat span{display:block;font-size:11px;color:#959bad}.stat strong{display:block;font-size:27px;margin-top:7px}
.chat{background:white;border:1px solid #ececf4;border-radius:17px;display:flex;flex-direction:column;flex:1;min-height:320px;overflow:hidden;box-shadow:0 8px 24px #22254106}
.chathead{display:flex;align-items:center;gap:11px;padding:15px 19px;border-bottom:1px solid #eff0f6}.chathead strong{font-size:13px}.chathead .muted{font-size:10px}
#messages{flex:1;overflow:auto;background:#fcfcff;padding:24px 21px;display:flex;flex-direction:column;gap:14px;min-height:160px}
.date{text-align:center;color:#a3a9b9;font-size:10px;margin:0 0 8px}
.msg{align-self:flex-start;max-width:80%;display:flex;flex-direction:column;align-items:flex-start;gap:5px}.msg.out{align-self:flex-end;align-items:flex-end}
.msg p{margin:0;background:#f0eff8;color:#393e55;padding:12px 15px;border-radius:14px 14px 14px 4px;line-height:1.55;font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere}
.msg.out p{background:#735de1;color:white;border-radius:14px 14px 4px 14px}.msg small{font-size:10px;color:#a7aaba}
.compose{padding:15px 18px;border-top:1px solid #eff0f5}.compose form{display:flex;gap:10px}.compose input{min-width:0;flex:1;padding:12px 13px;border:1px solid #e6e7ef;background:#fafaff;border-radius:11px;font-size:12px}
.send{background:#735de1;color:white;border:0;padding:12px 17px;border-radius:10px;font-weight:750;font-size:12px}
.note{font-size:10px;color:#9499ab;margin:9px 3px 0}.empty{padding:22px;font-size:12px;color:#9298aa}.reset{border:0;background:transparent;color:#7965d8;font-weight:800;font-size:11px;margin-left:auto}
@media(max-width:1050px){.layout{grid-template-columns:70px 285px minmax(0,1fr)}.side{padding:25px 12px}.brand{font-size:0}.brand b{font-size:20px}.side .small,.sidebottom,.nav{display:none}.content{padding:20px 16px}.top{padding:18px 16px}}
@media(max-width:700px){.layout{display:block}.side{display:none}.inbox{min-height:0;border-right:0}.inbox-head{padding:19px}.inbox-head h1{font-size:24px}.countline{padding:8px 19px}#conversations{display:flex;overflow-x:auto}.conversation{min-width:225px;max-width:255px;padding:12px 14px;border-right:1px solid #f0f1f6}.conversation.active{padding-left:11px}.work{height:680px}.content{padding:15px;gap:13px}.heading h2{font-size:21px}.stat{padding:12px}.stat strong{font-size:22px}.chat{min-height:370px}.badges{gap:4px}}

/* MOBILE-VERTICAL-INBOX-2 */
.back-to-inbox { display:none }

@media (max-width:700px) {
  .layout { height:100dvh; overflow:hidden }
  .inbox {
    height:100dvh;
    display:flex;
    overflow:hidden;
  }
  #conversations {
    display:block;
    flex:1;
    min-height:0;
    overflow-y:auto;
    overflow-x:hidden;
  }
  .conversation {
    width:100%;
    min-width:0;
    max-width:none;
    padding:17px 19px;
    border-right:0;
    border-bottom:1px solid #f0f1f6;
  }
  .conversation.active { padding-left:16px }
  .work { display:none; height:100dvh; overflow:hidden }

  .layout.chat-open .inbox { display:none }
  .layout.chat-open .work { display:flex }
  .layout.chat-open .top,
  .layout.chat-open .heading,
  .layout.chat-open .stats { display:none }

  .layout.chat-open .content {
    flex:1;
    min-height:0;
    padding:0;
    gap:0;
  }
  .layout.chat-open .chat {
    flex:1;
    min-height:0;
    border:0;
    border-radius:0;
  }
  .layout.chat-open #messages { min-height:0 }

  .back-to-inbox {
    display:inline-flex;
    background:#f2efff;
    color:#6950c6;
    border:0;
    border-radius:9px;
    padding:10px;
    font-size:12px;
    font-weight:750;
    white-space:nowrap;
  }
  .chathead { padding:12px }
}
</style>
</head><body>
<div class="layout">
<aside class="side"><div class="brand"><b>A</b> australigo</div><div><div class="small">Workspace</div><div class="nav">◉ &nbsp; Student inbox</div></div><div class="sidebottom"><strong><span class="dot">●</span> Teacher workspace</strong><div>One teacher · Demo preview</div><div>No real student data</div></div></aside>
<section class="inbox" aria-label="Student conversations"><div class="inbox-head"><div class="overline">Teacher workspace</div><h1>Inbox ✦</h1><div class="muted">Every student conversation, one calm place.</div><input class="search" id="search" placeholder="⌕  Search students or messages" aria-label="Search students"><div class="filters"><button class="filter on" data-mode="all">All chats</button><button class="filter" data-mode="unread">Unread</button></div></div><div class="countline" id="countline">Conversations</div><div id="conversations"></div></section>
<main class="work"><div class="top"><span class="crumb">Workspace / <strong>Teacher inbox</strong></span><span class="badges"><span class="badge">● DEMO MODE</span><span class="badge live">● Preview</span></span></div><div class="content"><div class="heading"><h2>Welcome back ☀️</h2><div class="muted">A little progress, one message at a time.</div></div><div class="stats"><div class="stat"><span>Students</span><strong id="students">0</strong></div><div class="stat"><span>Unread</span><strong id="unread">0</strong></div><div class="stat"><span>Replies sent</span><strong id="sent">0</strong></div></div><section class="chat" aria-label="Conversation"><div class="chathead"><button id="back-to-inbox" class="back-to-inbox" type="button">← Inbox</button><div class="avatar" id="avatar">ML</div><div><strong id="chatname">Maya L.</strong><div class="muted" id="level">English · Beginner</div></div><button class="reset" id="reset" type="button">Reset demo</button></div><div id="messages" aria-live="polite"></div><div class="compose"><form id="form"><input id="reply" maxlength="800" autocomplete="off" placeholder="Write a practice reply..." aria-label="Demo reply"><button class="send" type="submit">Send ↗</button></form><div class="note">Simulation only · Reply stays in this browser tab. No WhatsApp messages are sent.</div></div></section></div></main>
</div>
<script>
const samples=[
{id:1,name:'Maya L.',level:'English · Beginner',unread:2,msg:[['in','Hello teacher! Can you check a sentence?','09:41'],['in','I am learning English since two years.','09:42'],['out','Great effort! Say: I have been learning English for two years. 🌟','09:43'],['in','Thank you! Can we practice again?','09:45']]},
{id:2,name:'Noah T.',level:'French · Intermediate',unread:0,msg:[['in','Bonjour! Can we review passé composé?','10:08'],['out','Bien sûr! Let’s start with three examples.','10:10']]},
{id:3,name:'Lina P.',level:'English · Intermediate',unread:1,msg:[['in','What is the difference between say and tell?','11:01'],['out','I will explain with two easy examples.','11:03'],['in','Wonderful, thank you!','11:05']]},
{id:4,name:'Elio R.',level:'English · Beginner',unread:0,msg:[['out','Great speaking practice today!','Yesterday'],['in','Thanks! See you next lesson.','Yesterday']]}
];
let data=JSON.parse(JSON.stringify(samples)),selected=1,mode='all',sent=0;
const $=id=>document.getElementById(id);
function node(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e}
function render(){const q=$('search').value.trim().toLowerCase();const list=$('conversations');list.replaceChildren();const found=data.filter(c=>(mode==='all'||c.unread>0)&&(c.name.toLowerCase().includes(q)||c.msg.some(m=>m[1].toLowerCase().includes(q))));$('countline').textContent=found.length+' conversations';
for(const c of found){const b=node('button','conversation'+(c.id===selected?' active':''));b.type='button';const av=node('div','avatar',c.name.split(' ').map(x=>x[0]).join(''));const body=node('div','cbody');const top=node('div','crow');top.append(node('span','cname',c.name),node('span','ctime',c.msg.at(-1)[2]));body.append(top,node('div','cmeta',c.level));const bottom=node('div','crow');bottom.append(node('div','preview',c.msg.at(-1)[1]));if(c.unread)bottom.append(node('span','bubblecount',String(c.unread)));body.append(bottom);b.append(av,body);b.onclick=()=>{selected=c.id;c.unread=0;document.querySelector('.layout').classList.add('chat-open');render()};list.append(b)}if(!found.length)list.append(node('div','empty','No matching conversations.'));
$('students').textContent=data.length;$('unread').textContent=data.reduce((sum,c)=>sum+c.unread,0);$('sent').textContent=sent;showChat()}
function showChat(){const c=data.find(x=>x.id===selected);$('chatname').textContent=c.name;$('level').textContent=c.level;$('avatar').textContent=c.name.split(' ').map(x=>x[0]).join('');const area=$('messages');area.replaceChildren(node('div','date','SYNTHETIC CONVERSATION'));for(const m of c.msg){const wrap=node('div','msg'+(m[0]==='out'?' out':''));wrap.append(node('p','',m[1]),node('small','',m[2]));area.append(wrap)}area.scrollTop=area.scrollHeight}
$('search').oninput=render;document.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{mode=b.dataset.mode;document.querySelectorAll('[data-mode]').forEach(x=>x.classList.toggle('on',x===b));render()});
$('form').onsubmit=e=>{e.preventDefault();const input=$('reply');const text=input.value.trim();if(!text)return;const c=data.find(x=>x.id===selected);c.msg.push(['out',text,new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})]);input.value='';sent++;render()};
$('back-to-inbox').onclick=()=>document.querySelector('.layout').classList.remove('chat-open');
$('reset').onclick=()=>{data=JSON.parse(JSON.stringify(samples));selected=1;sent=0;mode='all';$('search').value='';document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('on',b.dataset.mode==='all'));render()};render();
</script></body></html>"""
