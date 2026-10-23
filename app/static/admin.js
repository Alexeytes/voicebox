function apiFetch(url, options={}) {
  const method=(options.method||'GET').toUpperCase();
  if(['POST','PUT','PATCH','DELETE'].includes(method)){const token=document.cookie.split('; ').find(row=>row.startsWith('vb_csrf='))?.split('=')[1]||'';options.headers={...(options.headers||{}),'X-CSRF-Token':decodeURIComponent(token)};}
  return fetch(url,options);
}
document.addEventListener('DOMContentLoaded', async () => {
  const stats = document.querySelector('#stats'), list = document.querySelector('#banners');
  async function refresh() {
    const results = await Promise.all([fetch('/admin/api/stats/overview?period=7d'), fetch('/admin/banners')]);
    if (!results[0].ok || !results[1].ok) { stats.textContent = 'Не удалось загрузить данные.'; return; }
    stats.textContent = JSON.stringify(await results[0].json(), null, 2);
    list.replaceChildren();
    for (const banner of await results[1].json()) {
      const item = document.createElement('li');
      item.append(document.createTextNode(banner.title + ' — ' + banner.position + ' — ' + (banner.enabled ? 'активен' : 'выключен') + ' '));
      const remove = document.createElement('button'); remove.textContent = 'Удалить';
      remove.onclick = async () => { await apiFetch('/admin/banners/' + banner.id, {method:'DELETE'}); await refresh(); };
      item.append(remove); list.append(item);
    }
  }
  document.querySelector('#banner-form').addEventListener('submit', async event => {
    event.preventDefault(); const form = event.currentTarget, button = form.querySelector('button'); button.disabled = true;
    try {
      const image = new FormData(); image.append('image', form.elements.image.files[0]);
      const uploaded = await apiFetch('/admin/banners/upload', {method:'POST', body:image}), asset = await uploaded.json();
      if (!uploaded.ok) throw new Error(asset.detail || asset.error);
      const campaign = new FormData();
      for (const field of ['title','target_url','alt_text','weight','position','html_snippet']) campaign.append(field, form.elements[field].value);
      for (const field of ['active_from','active_to']) { const value=form.elements[field].value; campaign.append(field,value?new Date(value).toISOString():''); }
      campaign.append('enabled',String(form.elements.enabled.checked));
      campaign.append('image_url', asset.url);
      const response = await apiFetch('/admin/banners', {method:'POST', body:campaign}), result = await response.json();
      if (!response.ok) throw new Error(result.detail || 'Не удалось сохранить баннер');
      document.querySelector('#message').textContent = 'Баннер добавлен.'; form.reset(); await refresh();
    } catch (error) { document.querySelector('#message').textContent = error.message; }
    finally { button.disabled = false; }
  });
  await refresh();
});
