'use strict';
const $=id=>document.getElementById(id), esc=x=>String(x??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=(v,n=1)=>v==null||!Number.isFinite(v)?'—':Number(v).toFixed(n);
const state={cohort:'KAC',rat:25,time:120,playing:false,loaded:new Map(),selected:[],generation:0,config:1,akRat:1};
let data,ak,audioContext,audioGain,audioSource,raf,last;
const labels={kac_d6:'KAC Day 6',kac_d8:'KAC Day 8',sp1:'SP1'};
async function json(url){const r=await fetch(url);if(!r.ok)throw Error(`Could not load ${url} (${r.status})`);return r.json();}
async function track(s){if(!state.loaded.has(s.id)){const r=await fetch('portal_data/'+s.track);if(!r.ok)throw Error(`Track unavailable for ${s.id}`);state.loaded.set(s.id,PortalMath.decode(await r.arrayBuffer(),s.frames));}return state.loaded.get(s.id);}
function metric(v,label,n=0){return `<div class="metric"><strong>${fmt(v,n)}</strong><span>${esc(label)}</span></div>`;}
function stop(){state.playing=false;cancelAnimationFrame(raf);$('play').textContent='Play ▶';$('play').setAttribute('aria-label','Play trajectories');}
function visibleSessions(){return data.sessions.filter(s=>s.cohort===state.cohort&&s.rat===state.rat).sort((a,b)=>a.cond.localeCompare(b.cond));}
function populateAnimals(){
 const rats=[...new Set(data.sessions.filter(s=>s.cohort===state.cohort).map(s=>s.rat))].sort((a,b)=>a-b);
 if(!rats.includes(state.rat))state.rat=rats[0];
 $('animal').innerHTML=rats.map(r=>`<option value="${r}" ${r===state.rat?'selected':''}>${r<=16?'M':'F'}${r}</option>`).join('');
}
async function choose(){
 stop();const gen=++state.generation;state.selected=visibleSessions();const snapshot=[...state.selected];
 $('load-status').textContent='Loading selected native-frame tracks…';$('play').disabled=true;$('open-data').disabled=true;$('pools').style.opacity='.5';
 try{await Promise.all(snapshot.map(track));if(gen!==state.generation)return;
  const keys=state.cohort==='KAC'?['kac_d6','kac_d8']:['sp1'];
  $('pools').classList.toggle('single',state.cohort==='SP1');
  $('pools').innerHTML=keys.map(cond=>{const s=snapshot.find(s=>s.cond===cond);return s?`<article class="pool-card"><header><h3>${labels[cond]} · ${s.sex}${s.rat}</h3><span>${s.fps} Hz / 120 s</span></header><canvas id="pool-${s.id}" width="700" height="700" role="img" aria-label="${labels[cond]}, ${s.sex}${s.rat}, tracked trajectory. Data and event table available below."></canvas><p id="frame-${s.id}" class="frame-status"></p></article>`:`<article class="pool-card missing"><h3>${labels[cond]} · M1</h3><p>No Day 6 cache available.<br>No trajectory is inferred.</p></article>`;}).join('');
  $('cohort-story').textContent=state.cohort==='KAC'?'KAC connects acquisition, Day 6 checking, the Day 7 reminder, and Day 8 checking. Compare the same animal across tests.':'SP1 is a separate cohort: 32 animals, shown in the confirmed 120-second window beginning at the existing placement marker. The same rat number does not identify a KAC animal.';
  $('load-status').textContent=`${state.cohort} · ${snapshot[0].sex}${state.rat} · ${snapshot.length===2?'paired tests':'one available test'} · native frames loaded`;
  $('pools').style.opacity='1';$('play').disabled=false;$('open-data').disabled=false;
  const last=snapshot.at(-1);$('profile-link').href='profiles.html?animal='+last.id;$('atlas-link').href='explorer.html?animal='+last.id;
  renderProfiles();renderSequences();sensitivity();draw();
 }catch(e){if(gen!==state.generation)return;$('load-status').textContent=e.message;}
}
function pool(canvas,s,t,time,hero=false){
 if(!canvas||!t)return;const ctx=canvas.getContext('2d');if(!ctx)return;
 const w=canvas.width,c=w/2,R=w*.407;ctx.clearRect(0,0,w,w);
 const point=(x,y)=>[c+(x-s.pool_px[0])/s.pool_px[2]*R,c+(y-s.pool_px[1])/s.pool_px[2]*R];
 const circle=(x,y,r,color,dash=[])=>{ctx.beginPath();ctx.setLineDash(dash);ctx.strokeStyle=color;ctx.lineWidth=1;ctx.arc(x,y,r,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);};
 circle(c,c,R,'#54868a');circle(c,c,R*.85,'#52777e28',[3,8]);
 ctx.strokeStyle='#64858b18';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(c-R,c);ctx.lineTo(c+R,c);ctx.moveTo(c,c-R);ctx.lineTo(c,c+R);ctx.stroke();
 const pl=point(...s.placement_px),goal=[c+s.p1_normalized[0]*R,c+s.p1_normalized[1]*R];
 const radius=hero?20:Number($('radius').value);
 circle(...pl,R*.165,'#81ddce88',[5,6]);circle(...goal,R*radius/86,'#e6bf7977',[2,6]);
 if(!hero){ctx.font=`${w*.017}px Segoe UI`;ctx.textAlign='center';ctx.fillStyle='#a7c9c8';ctx.fillText('PLACEMENT',pl[0],pl[1]+R*.165+19);ctx.fillStyle='#dbc69c';ctx.fillText('OLD GOAL · PROVISIONAL',goal[0],goal[1]-R*radius/86-12);}
 const end=Math.min(s.frames-1,Math.floor(time*s.fps)),raw=!hero&&$('path-mode').value==='raw';
 const ok=i=>raw?!(t.flags[i]&4)&&Number.isFinite(t.xy[4*i])&&Number.isFinite(t.xy[4*i+1]):!!(t.flags[i]&1);
 const pos=i=>point(t.xy[4*i+(raw?0:2)],t.xy[4*i+(raw?1:3)]);
 ctx.save();ctx.beginPath();ctx.arc(c,c,R+3,0,Math.PI*2);ctx.clip();
 // Segment type is split at every gap and every interpolation boundary.
 for(let kind=0;kind<2;kind++){
  if(raw&&kind)continue;ctx.beginPath();ctx.strokeStyle=kind?'#e6bf79':'#81ddce';ctx.globalAlpha=hero?.65:.8;ctx.lineWidth=hero?1.3:1.45;ctx.setLineDash(kind?[3,4]:[]);
  for(let i=1;i<=end;i++)if(ok(i)&&ok(i-1)){
   const filled=!raw&&!!((t.flags[i]|t.flags[i-1])&2);if(Number(filled)!==kind)continue;
   const a=pos(i-1),b=pos(i);ctx.moveTo(...a);ctx.lineTo(...b);
  }ctx.stroke();
 }
 ctx.globalAlpha=1;ctx.setLineDash([]);
 if(!hero&&$('rejected').checked){ctx.fillStyle='#fa987b';for(let i=0;i<=end;i++)if((t.flags[i]&4)&&Number.isFinite(t.xy[4*i])){const p=point(t.xy[4*i],t.xy[4*i+1]);ctx.beginPath();ctx.arc(...p,2,0,Math.PI*2);ctx.fill();}}
 if(ok(end)){const p=pos(end);ctx.fillStyle=(t.flags[end]&2)&&!raw?'#e6bf79':'#e6faf1';ctx.shadowColor=ctx.fillStyle;ctx.shadowBlur=14;ctx.beginPath();ctx.arc(...p,4,0,Math.PI*2);ctx.fill();ctx.shadowBlur=0;}
 ctx.restore();
 if(!hero){const f=t.flags[end],status=!(f&1)?'Unknown position':f&2?'Filled position · not directly observed':f&8?'Tracked off placement':'Tracked in placement region';$('frame-'+s.id).textContent=`${Math.min(time,120).toFixed(1)} s · source frame ${s.source_frame_start+end} · ${status}`;}
}
function draw(){
 $('clock').textContent=state.time.toFixed(1);$('time').value=state.time;
 state.selected.forEach(s=>pool($('pool-'+s.id),s,state.loaded.get(s.id),state.time));
 document.querySelectorAll('.cursor-line').forEach(l=>{const x=60+state.time/120*900;l.setAttribute('x1',x);l.setAttribute('x2',x);});
 if($('data-dialog').open)dataDetail();
}
function renderProfiles(){
 $('profiles').innerHTML=state.selected.map(s=>`<article class="profile-card"><h3>${labels[s.cond]} · ${s.sex}${s.rat} / WHOLE SESSION</h3><div class="metrics">${metric(s.head_sweeps_per_min,'Head sweeps / valid minute',1)}${metric(s.swim_seconds,'Observed swimming · s',1)}${metric(s.observed_placement_returns,'Observed placement returns')}${metric(s.complete_excursions,'Complete round trips')}${metric(s.area_successes,'Complete trips reaching old goal')}${metric(s.repeat_p1_trips,'Later goal-reaching trips · lower bound')}</div><p class="training">Unknown: ${fmt(s.pct_missing*1.2)} s · Filled: ${fmt(s.pct_interpolated*1.2)} s · Median complete round trip: ${fmt(s.median_round_trip_s)} s</p>${s.training.length?`<p class="training">Learning history · Day 1: ${fmt(s.training.find(t=>t.day===1)?.lat)} s → Day 5: ${fmt(s.training_d5_latency)} s → Day 7 reminder: ${fmt(s.training.find(t=>t.day===7)?.lat)} s mean latency. Day 7 follows Day 6 checking.</p>`:''}</article>`).join('');
}
function renderSequences(){
 $('sequences').innerHTML=state.selected.map(s=>{
  const events=s.return_timeline;const rows=Math.max(1,events.length),height=rows*27+55;
  let marks='';for(let k=0;k<=120;k+=20){const x=60+k/120*900;marks+=`<line x1="${x}" y1="20" x2="${x}" y2="${height-20}" stroke="#294349"/><text x="${x}" y="12" text-anchor="middle">${k}s</text>`;}
  events.forEach((e,i)=>{const y=32+i*27,x=60+e.start/120*900,len=(e.end-e.start)/120*900;marks+=`<text x="35" y="${y+5}" text-anchor="end">${e.number}</text><rect class="timeline-event" tabindex="0" role="button" aria-label="${esc(labels[s.cond])} segment ${e.number}, ${fmt(e.start)} to ${fmt(e.end)} seconds, ${e.complete?'complete':'incomplete'}. Jump to start." data-time="${e.start}" x="${x}" y="${y-5}" width="${Math.max(3,len)}" height="11" rx="2" fill="${e.complete?'#81ddce':'#748a91'}" opacity="${e.complete?'.9':'.6'}"><title>${e.complete?'Complete trip':'Incomplete segment'} ${e.number}: ${fmt(e.start)}–${fmt(e.end)} s</title></rect>`;if(e.p1_entry_s!=null)marks+=`<circle cx="${60+e.p1_entry_s/120*900}" cy="${y+.5}" r="4" fill="#e6bf79"/>`;});
  if(!events.length)marks+='<text x="70" y="40">No excursion segments observed.</text>';
  marks+=`<line class="cursor-line" x1="960" x2="960" y1="20" y2="${height-15}" stroke="#e7ece4" opacity=".6"/>`;
  const table=events.length?`<table><thead><tr><th>Segment</th><th>Start → end (s)</th><th>Departure known</th><th>Placement return</th><th>Complete</th><th>Old-goal entry (s)</th></tr></thead><tbody>${events.map(e=>`<tr><td><button data-time="${e.start}">${e.number} · replay</button></td><td>${fmt(e.start)} → ${fmt(e.end)}</td><td>${e.onset_known?'Yes':'No'}</td><td>${e.returned?'Yes':'Unresolved'}</td><td>${e.complete?'Yes':'No'}</td><td>${e.p1_entry_s==null?'Not observed':fmt(e.p1_entry_s)}</td></tr>`).join('')}</tbody></table>`:'<p class="quiet">No excursion segments observed in this window. Missing time, if present, remains unknown.</p>';
  return `<article class="sequence"><div class="sequence-head"><h3>${labels[s.cond]} · ${s.sex}${s.rat}</h3><p>${s.complete_excursions} complete trips · ${s.incomplete_segments} incomplete segments · fixed 20 cm / no dwell</p></div><svg viewBox="0 0 990 ${height}" role="group" aria-label="${labels[s.cond]} excursion timeline; each segment is keyboard selectable">${marks}</svg><details><summary>Read the sequence as a table</summary><div class="table-scroll">${table}</div></details></article>`;
 }).join('');
 $('sequences').querySelectorAll('[data-time]').forEach(el=>{const jump=()=>{stop();state.time=Number(el.dataset.time);draw();};el.addEventListener('click',jump);if(el.tagName.toLowerCase()==='rect')el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();jump();}});});
}
function sensitivity(){
 const radius=Number($('radius').value),dwell=Number($('dwell').value);$('radius-value').textContent=radius+' cm';$('dwell-value').textContent=dwell?dwell.toFixed(1)+' s':'Any entry';
 $('sensitivity-results').innerHTML=state.selected.map(s=>{const t=state.loaded.get(s.id);if(!t)return '';const q=PortalMath.area(t,s,radius,dwell,$('exclude-fill').checked);return `<article class="sensitivity-row"><h3>${labels[s.cond]} · ${s.sex}${s.rat} / FULL 120 s</h3><div class="metrics">${metric(q.entries,'Observed area entries')}${metric(q.episodes,'Qualifying bouts')}${metric(q.seconds,'Time in qualifying bouts · s',1)}</div><p class="micro">${q.unknownOnsets} bout onset(s) unknown or unobserved. ${$('exclude-fill').checked?'Filled frames excluded.':'Filled frames included as in the current analysis.'}</p></article>`;}).join('');draw();
}
function renderAK(){
 if(!ak)return;const max=Math.max(...ak.records.map(r=>r.passages),1),ys=v=>260-v/max*215,xs=c=>90+(c-1)*235;
 let svg='';for(let v=0;v<=max;v+=Math.max(1,Math.ceil(max/4))){svg+=`<line x1="60" y1="${ys(v)}" x2="590" y2="${ys(v)}" stroke="#294349"/><text x="45" y="${ys(v)+4}" text-anchor="end">${v}</text>`;}
 svg+='<text x="60" y="18">Software passages · PASSTH01</text>';
 for(let rat=1;rat<=30;rat++){const rr=ak.records.filter(r=>r.rat===rat).sort((a,b)=>a.configuration-b.configuration);svg+=`<polyline points="${rr.map(r=>xs(r.configuration)+','+ys(r.passages)).join(' ')}" fill="none" stroke="${rat===state.akRat?'#e6bf79':'#6a8d94'}" stroke-width="${rat===state.akRat?2.5:1}" opacity="${rat===state.akRat?1:.32}"/>`;}
 ak.means.forEach((m,i)=>{const x=xs(i+1);svg+=`<circle cx="${x}" cy="${ys(m)}" r="6" fill="#81ddce"/><text x="${x}" y="290" text-anchor="middle">Center ${i+1}</text><text x="${x+10}" y="${ys(m)-10}">Mean ${fmt(m,2)}</text>`;});
 ak.records.filter(r=>r.rat===state.akRat).forEach(r=>{svg+=`<circle cx="${xs(r.configuration)}" cy="${ys(r.passages)}" r="${r.configuration===state.config?6:4}" fill="#e6bf79"/>`;});
 $('ak-chart').innerHTML=svg;
 const r=ak.records.find(r=>r.rat===state.akRat&&r.configuration===state.config);
 $('ak-result').textContent=`Rat ${r.rat}: ${fmt(r.passages,0)} passages · mean ${fmt(ak.means[state.config-1],2)} (n = 30) · row ${r.source_row}`;
}
function dataDetail(){
 $('data-detail').innerHTML=state.selected.map(s=>{const i=Math.min(s.frames-1,Math.floor(state.time*s.fps)),t=state.loaded.get(s.id),f=t.flags[i];return `<article><h3>${labels[s.cond]} · ${s.sex}${s.rat}</h3><dl class="source-meta"><dt>Current frame</dt><dd>${i} in window; ${s.source_frame_start+i} in source; ${fmt(i/s.fps,3)} s after start</dd><dt>Window</dt><dd>${fmt(s.start_s,3)}–${fmt(s.start_s+120,3)} source seconds; ${s.frames} frames at ${s.fps} Hz; end exclusive</dd><dt>Unsmoothed (x, y)</dt><dd>${fmt(t.xy[i*4],3)}, ${fmt(t.xy[i*4+1],3)}</dd><dt>Processed (x, y)</dt><dd>${fmt(t.xy[i*4+2],3)}, ${fmt(t.xy[i*4+3],3)}</dd><dt>Quality flags</dt><dd>Valid processed: ${!!(f&1)} · filled: ${!!(f&2)} · original rejected: ${!!(f&4)} · off placement: ${!!(f&8)}</dd><dt>Model</dt><dd>${s.model}</dd><dt>Original track</dt><dd><code>${esc(s.tracking_source)}</code></dd><dt>Original SHA-256</dt><dd><code>${s.tracking_source_sha256}</code><br>${esc(s.source_hash_status)}</dd><dt>Cache</dt><dd><code>${esc(s.cache_file)}</code></dd><dt>Cache SHA-256</dt><dd><code>${s.cache_sha256}</code></dd><dt>Body selection</dt><dd>${esc(s.cache_raw_definition)}</dd><dt>Processing</dt><dd>Within-segment median smoothing; short fills up to 0.5 s; confidence, rim, false-spot and speed filters. Native time grid retained.</dd><dt>Geometry</dt><dd>172 cm analysis scale retained; former-goal registration pending. Display radius ${$('radius').value} cm. Complete-trip metrics remain at 20 cm, no dwell.</dd></dl></article>`;}).join('');
}
function downloadTracks(){
 const cols=['session','window_frame','source_frame','window_s','source_s','raw_x_px','raw_y_px','processed_x_px','processed_y_px','valid_processed','interpolated','rejected_original','off_placement'];
 const rows=[cols.join(',')];state.selected.forEach(s=>{const t=state.loaded.get(s.id);for(let i=0;i<s.frames;i++){const f=t.flags[i];rows.push([s.id,i,s.source_frame_start+i,i/s.fps,(s.source_frame_start+i)/s.fps,...Array.from(t.xy.slice(i*4,i*4+4)).map(v=>Number.isFinite(v)?v:''),Number(!!(f&1)),Number(!!(f&2)),Number(!!(f&4)),Number(!!(f&8))].join(','));}});
 const blob=new Blob([rows.join('\n')],{type:'text/csv;charset=utf-8'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`return_${state.cohort}_${state.rat}_native_frames.csv`;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000);
}
function tick(now){if(!state.playing)return;state.time=Math.min(120,state.time+(now-last)/1000*Number($('speed').value));last=now;draw();if(state.time>=120)stop();else raf=requestAnimationFrame(tick);}
async function toggleSound(){
 try{if(!audioContext){const AC=window.AudioContext||window.webkitAudioContext;if(!AC)throw Error('Audio unavailable');audioContext=new AC();const buffer=audioContext.createBuffer(1,audioContext.sampleRate*4,audioContext.sampleRate),b=buffer.getChannelData(0);let value=0;for(let i=0;i<b.length;i++){value=.98*value+.02*(Math.random()*2-1);b[i]=value;}audioSource=audioContext.createBufferSource();audioSource.buffer=buffer;audioSource.loop=true;const filter=audioContext.createBiquadFilter();filter.type='lowpass';filter.frequency.value=450;audioGain=audioContext.createGain();audioGain.gain.value=0;audioSource.connect(filter).connect(audioGain).connect(audioContext.destination);audioSource.start();}
 await audioContext.resume();const on=$('sound').getAttribute('aria-pressed')!=='true';audioGain.gain.setTargetAtTime(on?.35:0,audioContext.currentTime,.1);$('sound').setAttribute('aria-pressed',String(on));$('sound').textContent=on?'Sound on':'Sound off';
 }catch(e){$('sound').textContent='Sound unavailable';$('sound').disabled=true;}
}
async function init(){
 data=await json('portal_data/sessions.json');populateAnimals();await choose();
 const hero=data.sessions.find(s=>s.id==='kac_d8_25');pool($('hero'),hero,await track(hero),120,true);
 document.querySelectorAll('[data-cohort]').forEach(b=>b.addEventListener('click',()=>{state.cohort=b.dataset.cohort;document.querySelectorAll('[data-cohort]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});populateAnimals();choose();}));
 $('animal').addEventListener('change',()=>{state.rat=Number($('animal').value);choose();});
 ['path-mode','rejected'].forEach(id=>$(id).addEventListener('change',draw));
 $('time').addEventListener('input',()=>{stop();state.time=Number($('time').value);draw();});
 $('play').addEventListener('click',()=>{if(state.playing){stop();return;}if(state.time>=120)state.time=0;state.playing=true;last=performance.now();$('play').textContent='Pause Ⅱ';$('play').setAttribute('aria-label','Pause trajectories');raf=requestAnimationFrame(tick);});
 ['radius','dwell','exclude-fill'].forEach(id=>$(id).addEventListener('input',sensitivity));
 $('reset-definition').addEventListener('click',()=>{$('radius').value=20;$('dwell').value=0;$('exclude-fill').checked=false;sensitivity();});
 $('open-data').addEventListener('click',()=>{stop();dataDetail();$('data-dialog').showModal();});$('close-data').addEventListener('click',()=>$('data-dialog').close());$('download-track').addEventListener('click',downloadTracks);
 $('sound').addEventListener('click',toggleSound);
 document.addEventListener('visibilitychange',()=>{if(document.hidden){stop();if(audioGain){audioGain.gain.setTargetAtTime(0,audioContext.currentTime,.1);$('sound').setAttribute('aria-pressed','false');$('sound').textContent='Sound off';}}});
 ak=await json('portal_data/ak1.json');$('ak-animal').innerHTML=Array.from({length:30},(_,i)=>`<option value="${i+1}">Rat ${i+1}</option>`).join('');
 $('ak-animal').addEventListener('change',()=>{state.akRat=Number($('ak-animal').value);renderAK();});
 document.querySelectorAll('[data-config]').forEach(b=>b.addEventListener('click',()=>{state.config=Number(b.dataset.config);document.querySelectorAll('[data-config]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});renderAK();}));
 $('ak-table').innerHTML='<table><thead><tr><th>Animal</th><th>Center 1 passages (row)</th><th>Center 2 passages (row)</th><th>Center 3 passages (row)</th><th>Path distance · m</th></tr></thead><tbody>'+Array.from({length:30},(_,i)=>{const rr=ak.records.filter(r=>r.rat===i+1).sort((a,b)=>a.configuration-b.configuration);return `<tr><td>Rat ${i+1}</td>${rr.map(r=>`<td>${fmt(r.passages,0)} (${r.source_row})</td>`).join('')}<td>${fmt(rr[0].path_m,2)}</td></tr>`;}).join('')+'</tbody></table>';renderAK();
 document.documentElement.dataset.portalReady='true';
}
init().catch(e=>{$('load-status').textContent=e.message+' — reload to retry. The existing dashboard remains available.';console.error(e);});
