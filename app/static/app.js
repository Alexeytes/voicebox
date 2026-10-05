document.addEventListener('DOMContentLoaded', function() {
  const langSelect = document.getElementById('lang-select');
  const voiceSelect = document.getElementById('voice-select');
  const previewBtn = document.getElementById('preview-btn');
  const synthForm = document.getElementById('tts-form');
  const statusDiv = document.getElementById('status');
  const player = document.getElementById('player');
  let polling = null;

  // Загрузка голосов
  async function loadVoices() {
    const lang = langSelect.value;
    const res = await fetch(`/voices?lang=${lang}`);
    const voices = await res.json();
    voiceSelect.innerHTML = '';
    const groups = {};
    voices.forEach(v => {
      if(!groups[v.engine]) groups[v.engine] = [];
      groups[v.engine].push(v);
    });
    Object.keys(groups).forEach(engine => {
      const optgroup = document.createElement('optgroup');
      optgroup.label = engine;
      groups[engine].forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.textContent = v.name;
        optgroup.appendChild(opt);
      });
      voiceSelect.appendChild(optgroup);
    });
  }

  langSelect.onchange = loadVoices;
  loadVoices();

  previewBtn.onclick = async (e) => {
    e.preventDefault();
    previewBtn.disabled = true;
    statusDiv.textContent = 'Генерация превью...';
    const formData = new FormData();
    formData.append('voice_id', voiceSelect.value);
    const resp = await fetch('/voices/preview', { method: 'POST', body: formData });
    if (resp.ok) {
      const blob = await resp.blob();
      player.src = URL.createObjectURL(blob);
      player.style.display = '';
      player.play();
      statusDiv.textContent = 'Превью готово!';
    } else {
      statusDiv.textContent = 'Ошибка при генерации превью';
    }
    previewBtn.disabled = false;
  };

  synthForm.onsubmit = async (e) => {
    e.preventDefault();
    statusDiv.textContent = 'Отправка...';
    player.style.display = 'none';
    let formData = new FormData(synthForm);
    let resp = await fetch('/synthesize', { method: 'POST', body: formData });
    let data = await resp.json();
    if (data.error) {
      statusDiv.textContent = 'Ошибка: ' + data.error;
      return;
    }
    statusDiv.textContent = 'Генерация...';
    polling = setInterval(awaitStatus, 1000, data.job_id);
  };

  async function awaitStatus(job_id) {
    let resp = await fetch('/status/' + job_id);
    let res = await resp.json();
    if (res.status === 'done' && res.url) {
      clearInterval(polling);
      statusDiv.textContent = 'Готово!';
      player.src = res.url;
      player.style.display = '';
    } else if (res.status === 'error') {
      clearInterval(polling);
      statusDiv.textContent = 'Ошибка: ' + (res.error || 'Неизвестно');
    } else {
      statusDiv.textContent = 'В очереди или прогресс...';
    }
  }
});
