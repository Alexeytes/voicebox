document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('#tts-form');
  const language = document.querySelector('#lang-select');
  const voice = document.querySelector('#voice-select');
  const style = document.querySelector('#style-select');
  const preview = document.querySelector('#preview-btn');
  const status = document.querySelector('#result-panel');
  const file = document.querySelector('#book-file');
  const text = document.querySelector('#book-text');
  const player = document.querySelector('#player');
  const previewPlayer = document.querySelector('#preview-player');
  let previewUrl = null;
  let selectedVoice = null;
  let cancelPolling = false;

  function setStatus(message, showProgress = false) {
    status.querySelector('.result-empty').hidden = false;
    status.querySelector('.result-empty h2').textContent = message;
    status.querySelector('.result-empty p').textContent = '';
    status.querySelector('#result-content').hidden = true;
    if (showProgress) status.querySelector('#job-progress').hidden = false;
  }
  function updateVoiceInfo() {
    const current = selectedVoice;
    const note = document.querySelector('#voice-note');
    const isAzure = current?.engine === 'azure-speech';
    const isGtts = current?.engine === 'gtts';
    [...style.options].forEach(option => { option.disabled = !isAzure && option.value !== 'natural'; });
    if (!isAzure && style.value !== 'natural') style.value = 'natural';
    if (isAzure) note.textContent = 'Выберите нейтральный, вдумчивый или серьёзный стиль чтения.';
    else if (isGtts) note.textContent = 'Базовый голос может звучать более механически. Для естественного чтения выберите Edge Neural.';
    else note.textContent = 'Edge Neural: нейронный голос с естественным темпом. Эмоциональные стили доступны в Azure.';
  }
  async function loadVoices() {
    voice.innerHTML = '<option>Загружаю…</option>';
    try {
      const response = await fetch('/voices?lang=' + encodeURIComponent(language.value));
      if (!response.ok) throw new Error('Ошибка загрузки голосов');
      const voices = await response.json();
      voice.replaceChildren();
      const groups = new Map();
      for (const item of voices) {
        if (!groups.has(item.engine)) groups.set(item.engine, []);
        groups.get(item.engine).push(item);
      }
      for (const [engine, items] of groups) {
        const group = document.createElement('optgroup');
        group.label = engine === 'azure-speech' ? 'Azure · выразительные' : engine === 'edge-tts' ? 'Edge Neural' : 'Базовые';
        for (const item of items) {
          const option = document.createElement('option'); option.value = item.id; option.textContent = item.name;
          group.append(option);
        }
        voice.append(group);
      }
      selectedVoice = voices.find(v => v.id === voice.value);
      updateVoiceInfo();
    } catch (error) {
      voice.innerHTML = '<option value="gtts:' + language.value + '">Базовый голос</option>';
      selectedVoice = {engine: 'gtts'}; updateVoiceInfo();
      setStatus('Не удалось загрузить список голосов');
    }
  }
  language.addEventListener('change', loadVoices);
  voice.addEventListener('change', () => { selectedVoice = null;
    // Re-read the selected voice from cached group data returned by the API.
    fetch('/voices?lang=' + encodeURIComponent(language.value)).then(r => r.json()).then(vs => {selectedVoice = vs.find(v => v.id === voice.value); updateVoiceInfo();});
  });
  text.addEventListener('input', () => {
    if (text.value) { file.value = ''; document.querySelector('#file-label').textContent = 'Загрузить книгу'; }
    document.querySelector('#char-count').textContent = text.value.length.toLocaleString('ru-RU') + ' символов';
  });
  file.addEventListener('change', () => {
    const chosen = file.files[0];
    document.querySelector('#file-label').textContent = chosen ? chosen.name : 'Загрузить книгу';
    if (chosen) { text.value = ''; document.querySelector('#char-count').textContent = '0 символов'; }
  });
  preview.addEventListener('click', async () => {
    preview.disabled = true; preview.querySelector('span').textContent = 'Готовлю образец…';
    try {
      const body = new FormData(); body.append('voice_id', voice.value); body.append('style', style.value);
      const response = await fetch('/voices/preview', {method:'POST', body});
      if (!response.ok) throw new Error((await response.json()).detail || 'Не удалось создать образец');
      const blob = await response.blob(); if (previewUrl) URL.revokeObjectURL(previewUrl);
      previewUrl = URL.createObjectURL(blob); previewPlayer.src = previewUrl; previewPlayer.hidden = false; await previewPlayer.play();
      document.querySelector('#voice-note').textContent = 'Образец выбранного голоса воспроизводится.';
    } catch (error) { document.querySelector('#voice-note').textContent = error.message; }
    finally { preview.disabled = false; preview.querySelector('span').textContent = 'Образец голоса'; }
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    const button = form.querySelector('button[type=submit]'); button.disabled = true;
    status.querySelector('#job-progress').hidden = true; setStatus('Загружаю материал…');
    try {
      const response = await fetch('/synthesize', {method:'POST', body:new FormData(form)});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || data.error || 'Не удалось начать озвучивание');
      cancelPolling = false; setStatus('Синтезирую речь…', true);
      await poll(data.job_id, data.words);
    } catch (error) { status.querySelector('#job-progress').hidden = true; setStatus(error.message); }
    finally { button.disabled = false; }
  });
  document.querySelector('#cancel-poll').addEventListener('click', () => { cancelPolling = true; setStatus('Ожидание остановлено. Синтез продолжается на сервере.', true); });
  async function poll(jobId, words) {
    for (;;) {
      if (cancelPolling) return;
      await new Promise(resolve => setTimeout(resolve, 1200));
      const response = await fetch('/status/' + encodeURIComponent(jobId));
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'Задача недоступна');
      if (result.status === 'error') { status.querySelector('#job-progress').hidden = true; throw new Error(result.error || 'Ошибка синтеза'); }
      document.querySelector('#progress-bar').value = result.progress || 0;
      document.querySelector('#progress-label').textContent = result.status === 'queued' ? 'Задача в очереди…' : 'Синтезирую… ' + result.progress + '%';
      if (result.status === 'done') {
        status.querySelector('#job-progress').hidden = true; status.querySelector('.result-empty').hidden = true;
        const content = status.querySelector('#result-content'); content.hidden = false;
        player.src = result.url; player.hidden = false;
        const link = document.querySelector('#download-link'); link.href = result.url; link.download = 'voicebox-' + jobId + '.mp3';
        document.querySelector('#stat-words').textContent = Number(words || result.words).toLocaleString('ru-RU');
        document.querySelector('#stat-time').textContent = Math.max(1, Math.round(result.elapsed_ms / 1000)) + ' сек';
        document.querySelector('#stat-duration').textContent = Math.max(1, Math.round((result.audio_seconds || result.estimated_audio_seconds) / 60)) + ' мин';
        saveHistory({url:result.url,words:result.words,voice:voice.value,created:Date.now()});
        return;
      }
      setStatus(result.status === 'queued' ? 'Задача в очереди…' : 'Синтезирую… ' + result.progress + '%', true);
    }
  }
  function saveHistory(item) {
    try { const saved=JSON.parse(localStorage.getItem('voicebox-history')||'[]'); saved.unshift(item); localStorage.setItem('voicebox-history',JSON.stringify(saved.slice(0,5))); renderHistory(); } catch {}
  }
  function renderHistory() {
    try { const items=JSON.parse(localStorage.getItem('voicebox-history')||'[]').filter(x=>/^\/audio\/[a-f0-9]{32}\.mp3$/.test(x.url)); const panel=document.querySelector('#history'), list=document.querySelector('#history-list'); list.replaceChildren(); panel.hidden=!items.length;
      for(const item of items){const li=document.createElement('li');const button=document.createElement('button');button.textContent=new Date(item.created).toLocaleString('ru-RU')+' · '+item.words+' слов';button.onclick=()=>{player.src=item.url;player.play().catch(()=>{});};li.append(button);list.append(li);}
    } catch {}
  }
  async function loadAds() {
    for (const slot of document.querySelectorAll('.ad-slot')) {
      try {
        const response = await fetch('/ads?position=' + encodeURIComponent(slot.dataset.position));
        const banners = await response.json(); if (!response.ok || !banners.length) {slot.hidden = true; continue;}
        slot.replaceChildren();
        for (const banner of banners) {
          if (banner.html_snippet) { const link=document.createElement("a"); link.href=banner.click_url; link.rel="sponsored noopener"; link.target="_blank"; link.innerHTML=banner.html_snippet; slot.append(link); continue; }
          const link = document.createElement('a'); link.href = banner.click_url; link.rel = 'sponsored noopener'; link.target = '_blank';
          const image = document.createElement('img'); image.src = banner.image_url; image.alt = banner.alt_text || banner.title; image.loading = 'lazy';
          link.append(image); if (banner.title) {const label = document.createElement('span'); label.textContent = banner.title; link.append(label);} slot.append(link);
        }
        slot.hidden = false;
      } catch { slot.hidden = true; }
    }
  }
  renderHistory(); loadVoices(); loadAds();
  window.setInterval(loadAds, 30000);
});
