document.addEventListener('DOMContentLoaded', () => {
 let period='7d', offset=0; const cards=document.querySelector('#cards'), events=document.querySelector('#events'), chart=document.querySelector('#chart');
 async function load(){
  const results=await Promise.all([fetch('/admin/api/stats/overview?period='+period),fetch('/admin/api/stats/timeseries?metric=synthesis&range='+period),fetch('/admin/api/stats/events?limit=50&offset='+offset+'&event_type='+encodeURIComponent(document.querySelector('#event-filter').value))]);
  if(results.some(r=>!r.ok)){cards.textContent='Не удалось загрузить статистику.';return;}
  const data=await results[0].json(); cards.replaceChildren();
  for(const pair of [['Синтезировано',data.synthesis_done],['Ошибки',data.synthesis_errors],['Среднее время',Math.round(data.average_duration_ms/1000)+' сек'],['Показы рекламы',data.banner_impressions],['Переходы',data.banner_clicks],['CTR',data.banner_ctr_percent+'%']]){const card=document.createElement('div');card.style.cssText='display:inline-block;min-width:130px;margin:8px;padding:16px;background:#182330;border-radius:10px';const value=document.createElement('b');value.textContent=pair[1];const label=document.createElement('div');label.textContent=pair[0];card.append(value,label);cards.append(card);}
  const points=await results[1].json(), max=Math.max(1,...points.map(point=>point.count)), width=800, height=150;chart.replaceChildren();const path=document.createElementNS('http://www.w3.org/2000/svg','polyline');path.setAttribute('fill','none');path.setAttribute('stroke','#9be5c1');path.setAttribute('stroke-width','3');path.setAttribute('points',points.map((point,i)=>(points.length<2?width/2:i*width/(points.length-1))+','+(height-(point.count/max)*(height-20))).join(' '));chart.append(path);
  events.replaceChildren();for(const item of (await results[2].json()).items){const tr=document.createElement('tr');for(const key of ['ts','event_type','lang','voice_id','status']){const td=document.createElement('td');td.textContent=item[key]||'—';tr.append(td);}events.append(tr);}
 }
 document.querySelectorAll('[data-period]').forEach(button=>button.addEventListener('click',()=>{period=button.dataset.period;load();}));
 document.querySelector('#event-filter').addEventListener('change',()=>{offset=0;load();});
 document.querySelector('#events-prev').addEventListener('click',()=>{offset=Math.max(0,offset-50);load();});
 document.querySelector('#events-next').addEventListener('click',()=>{offset+=50;load();});load();
});
