async function fetchRestock() {
  const resp = await fetch('/restock');
  if (!resp.ok) {
    document.getElementById('status').textContent = 'Error fetching restock';
    return;
  }
  const data = await resp.json();
  document.getElementById('status').textContent = 'Loaded';

  const shopping = document.getElementById('shopping');
  shopping.innerHTML = '';
  for (const [vendor, entries] of Object.entries(data.shopping_by_vendor || {})) {
    const wrap = document.createElement('div');
    wrap.className = 'vendor';
    const h = document.createElement('h3');
    h.textContent = vendor;
    wrap.appendChild(h);
    entries.forEach(e => {
      const d = document.createElement('div');
      d.className = 'item' + (e.below_minimum ? ' below' : '');
      d.textContent = e.name + (e.type === 'item' ? ` — ${e.on_hand} on hand (min ${e.minimum_quantity})` : ` — ${e.reason || ''}`);
      wrap.appendChild(d);
    });
    shopping.appendChild(wrap);
  }

  const auto = document.getElementById('auto');
  auto.innerHTML = '';
  (data.auto || []).forEach(i => {
    const d = document.createElement('div');
    d.className = 'item below';
    d.textContent = `${i.name} — ${i.on_hand} on hand (min ${i.minimum_quantity}) — ${i.storage_area}`;
    auto.appendChild(d);
  });

  const manual = document.getElementById('manual');
  manual.innerHTML = '';
  (data.manual || []).forEach(e => {
    const d = document.createElement('div');
    d.className = 'item';
    d.textContent = `${e.name} — ${e.vendor_name} ${e.storage_area ? ' — ' + e.storage_area : ''} ${e.reason ? ' — ' + e.reason : ''}`;
    manual.appendChild(d);
  });
}

window.addEventListener('load', () => {
  fetchRestock();
  setInterval(fetchRestock, 30_000);
});
