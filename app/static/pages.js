// Utility functions
function setStatus(msg) {
  document.getElementById('status').textContent = msg;
}

// Restock handlers
async function handleRestock(containerPrefix = '') {
  try {
    const resp = await fetch('/restock');
    if (!resp.ok) {
      setStatus('Restock API error');
      const err = await resp.json().catch(() => ({}));
      const autoEl = document.getElementById((containerPrefix?containerPrefix+'-':'')+'auto');
      if (autoEl) autoEl.textContent = err.message || 'No data';
      return;
    }
    const data = await resp.json();
    setStatus('Loaded');

    const shopping = document.getElementById((containerPrefix?containerPrefix+'-':'')+'shopping');
    if (shopping) {
      shopping.innerHTML = '';
      if (Object.keys(data.shopping_by_vendor || {}).length === 0) {
        shopping.innerHTML = '<div class="empty-state">No items to restock</div>';
      } else {
        for (const [vendor, entries] of Object.entries(data.shopping_by_vendor || {})) {
          const wrap = document.createElement('div');
          wrap.className = 'vendor-group';
          const h = document.createElement('h4');
          h.textContent = vendor;
          wrap.appendChild(h);
          entries.forEach(e => {
            const d = document.createElement('div');
            d.className = 'item' + (e.below_minimum ? ' below' : '');
            const info = document.createElement('div');
            info.className = 'item-info';
            info.textContent = e.name + (e.type === 'item' ? ` — ${e.on_hand} on hand (min ${e.minimum_quantity})` : ` — ${e.reason || ''}`);
            d.appendChild(info);
            wrap.appendChild(d);
          });
          shopping.appendChild(wrap);
        }
      }
    }

    const auto = document.getElementById((containerPrefix?containerPrefix+'-':'')+'auto');
    if (auto) {
      auto.innerHTML = '';
      if ((data.auto || []).length === 0) {
        auto.innerHTML = '<div class="empty-state">All items above minimum</div>';
      } else {
        (data.auto || []).forEach(i => {
          const d = document.createElement('div');
          d.className = 'item below';
          const info = document.createElement('div');
          info.className = 'item-info';
          info.textContent = `${i.name} — ${i.on_hand} on hand (min ${i.minimum_quantity}) — ${i.storage_area}`;
          d.appendChild(info);
          auto.appendChild(d);
        });
      }
    }

    const manual = document.getElementById((containerPrefix?containerPrefix+'-':'')+'manual');
    if (manual) {
      manual.innerHTML = '';
      if ((data.manual || []).length === 0) {
        manual.innerHTML = '<div class="empty-state">No manual entries</div>';
      } else {
        (data.manual || []).forEach(e => {
          const d = document.createElement('div');
          d.className = 'item';
          const info = document.createElement('div');
          info.className = 'item-info';
          info.textContent = `${e.name} — ${e.vendor_name} ${e.storage_area ? ' — ' + e.storage_area : ''} ${e.reason ? ' — ' + e.reason : ''}`;
          d.appendChild(info);
          
          const actions = document.createElement('div');
          actions.className = 'item-actions';
          const resolveBtn = document.createElement('button');
          resolveBtn.textContent = 'Resolve';
          resolveBtn.className = 'small secondary';
          resolveBtn.onclick = () => resolveManualEntry(e.id);
          const deleteBtn = document.createElement('button');
          deleteBtn.textContent = 'Delete';
          deleteBtn.className = 'small danger';
          deleteBtn.onclick = () => deleteManualEntry(e.id);
          actions.appendChild(resolveBtn);
          actions.appendChild(deleteBtn);
          d.appendChild(actions);
          
          manual.appendChild(d);
        });
      }
    }
  } catch (err) {
    setStatus('Error: ' + err.message);
  }
}

async function resolveManualEntry(entryId) {
  try {
    const resp = await fetch(`/restock/${entryId}/resolve`, { method: 'POST' });
    if (resp.ok) {
      setStatus('Entry resolved');
      handleRestock('');
    } else {
      setStatus('Failed to resolve');
    }
  } catch (err) {
    setStatus('Error: ' + err.message);
  }
}

async function deleteManualEntry(entryId) {
  if (!confirm('Delete this manual entry?')) return;
  try {
    const resp = await fetch(`/restock/${entryId}`, { method: 'DELETE' });
    if (resp.ok) {
      setStatus('Entry deleted');
      handleRestock('');
    } else {
      setStatus('Failed to delete');
    }
  } catch (err) {
    setStatus('Error: ' + err.message);
  }
}

// Vendors
async function loadVendors() {
  const resp = await fetch('/vendors');
  const container = document.getElementById('vendors-list');
  if (!resp.ok) { 
    if (container) container.textContent = 'Error loading'; 
    return; 
  }
  const data = await resp.json();
  
  if (container) {
    container.innerHTML = '';
    if (data.length === 0) {
      container.innerHTML = '<div class="empty-state">No vendors yet. Add one above!</div>';
    } else {
      data.forEach(v => {
        const d = document.createElement('div');
        d.className = 'item';
        const info = document.createElement('div');
        info.className = 'item-info';
        info.textContent = v.name;
        d.appendChild(info);
        
        const actions = document.createElement('div');
        actions.className = 'item-actions';
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.className = 'small danger';
        deleteBtn.onclick = () => deleteVendor(v.id);
        actions.appendChild(deleteBtn);
        d.appendChild(actions);
        
        container.appendChild(d);
      });
    }
  }
  
  // Update vendor dropdowns
  updateVendorDropdowns(data);
  return data;
}

function updateVendorDropdowns(vendors) {
  const selects = document.querySelectorAll('#area-vendor, #item-vendor, #manual-vendor');
  selects.forEach(select => {
    const currentValue = select.value;
    const noneOption = select.querySelector('option[value=""]');
    select.innerHTML = '';
    if (noneOption) select.appendChild(noneOption.cloneNode(true));
    vendors.forEach(v => {
      const opt = document.createElement('option');
      opt.value = v.id;
      opt.textContent = v.name;
      select.appendChild(opt);
    });
    select.value = currentValue;
  });
}

async function deleteVendor(vendorId) {
  if (!confirm('Delete this vendor? This may affect storage areas and items.')) return;
  try {
    const resp = await fetch(`/vendors/${vendorId}`, { method: 'DELETE' });
    if (resp.ok) {
      setStatus('Vendor deleted');
      loadVendors();
    } else {
      setStatus('Failed to delete vendor');
    }
  } catch (err) {
    setStatus('Error: ' + err.message);
  }
}

// Storage Areas
async function loadStorageAreas() {
  const resp = await fetch('/storage-areas');
  const container = document.getElementById('areas');
  if (!resp.ok) { 
    if (container) container.textContent = 'Error loading'; 
    return; 
  }
  const data = await resp.json();
  
  if (container) {
    container.innerHTML = '';
    if (data.length === 0) {
      container.innerHTML = '<div class="empty-state">No storage areas yet. Add one above!</div>';
    } else {
      data.forEach(a => {
        const d = document.createElement('div');
        d.className = 'item';
        const info = document.createElement('div');
        info.className = 'item-info';
        info.textContent = `${a.name} (${a.items.length} items)${a.vendor_name ? ' — Default: '+a.vendor_name : ''}`;
        d.appendChild(info);
        
        const actions = document.createElement('div');
        actions.className = 'item-actions';
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.className = 'small danger';
        deleteBtn.onclick = () => deleteStorageArea(a.id);
        actions.appendChild(deleteBtn);
        d.appendChild(actions);
        
        container.appendChild(d);
      });
    }
  }
  
  // Update storage area dropdowns
  updateStorageAreaDropdowns(data);
  return data;
}

function updateStorageAreaDropdowns(areas) {
  const selects = document.querySelectorAll('#item-storage-area, #manual-storage-area');
  selects.forEach(select => {
    const currentValue = select.value;
    const hasNone = select.querySelector('option[value=""]');
    select.innerHTML = '';
    if (hasNone) {
      const noneOpt = document.createElement('option');
      noneOpt.value = '';
      noneOpt.textContent = hasNone.textContent;
      select.appendChild(noneOpt);
    }
    areas.forEach(a => {
      const opt = document.createElement('option');
      opt.value = a.id;
      opt.textContent = a.name;
      select.appendChild(opt);
    });
    select.value = currentValue;
  });
}

async function deleteStorageArea(areaId) {
  if (!confirm('Delete this storage area? All items in it will also be deleted.')) return;
  try {
    const resp = await fetch(`/storage-areas/${areaId}`, { method: 'DELETE' });
    if (resp.ok) {
      setStatus('Storage area deleted');
      loadStorageAreas();
    } else {
      setStatus('Failed to delete storage area');
    }
  } catch (err) {
    setStatus('Error: ' + err.message);
  }
}

// Items
async function loadItems() {
  const resp = await fetch('/items');
  const container = document.getElementById('items-list');
  if (!resp.ok) { 
    if (container) container.textContent = 'Error loading'; 
    return; 
  }
  const data = await resp.json();
  
  if (container) {
    container.innerHTML = '';
    if (data.length === 0) {
      container.innerHTML = '<div class="empty-state">No items yet. Add one above!</div>';
    } else {
      data.forEach(i => {
        const d = document.createElement('div');
        d.className = 'item' + (i.below_minimum ? ' below' : '');
        
        const info = document.createElement('div');
        info.className = 'item-info';
        info.innerHTML = `
          <strong>${i.name}</strong><br>
          <small>On hand: ${i.on_hand} | Min: ${i.minimum_quantity} | ${i.storage_area_name || 'No area'}${i.vendor_name ? ' | '+i.vendor_name : ''} | Tracking: ${i.tracking_method}${i.tracking_method === 'binary' ? (i.is_low ? ' (LOW)' : '') : ''}</small>
        `;
        d.appendChild(info);
        
        const actions = document.createElement('div');
        actions.className = 'item-actions';
        
        const decrementBtn = document.createElement('button');
        decrementBtn.textContent = '−';
        decrementBtn.className = 'small';
        decrementBtn.onclick = () => adjustItemQuantity(i.id, -1);
        
        const incrementBtn = document.createElement('button');
        incrementBtn.textContent = '+';
        incrementBtn.className = 'small';
        incrementBtn.onclick = () => adjustItemQuantity(i.id, 1);
        
        const setBtn = document.createElement('button');
        setBtn.textContent = 'Set';
        setBtn.className = 'small secondary';
        setBtn.onclick = () => setItemQuantity(i.id, i.on_hand);
        
        const deleteBtn = document.createElement('button');
        deleteBtn.textContent = 'Delete';
        deleteBtn.className = 'small danger';
        deleteBtn.onclick = () => deleteItem(i.id);
        
        actions.appendChild(decrementBtn);
        actions.appendChild(incrementBtn);
        actions.appendChild(setBtn);
        actions.appendChild(deleteBtn);
        // If binary tracked, show low toggle
        if (i.tracking_method === 'binary') {
          const lowToggle = document.createElement('input');
          lowToggle.type = 'checkbox';
          lowToggle.checked = !!i.is_low;
          lowToggle.title = 'Mark as low';
          lowToggle.style.marginLeft = '8px';
          lowToggle.onchange = async () => {
            try {
              const r = await fetch(`/items/${i.id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_low: lowToggle.checked })
              });
              if (r.ok) {
                setStatus('Updated low flag');
                loadItems();
                handleRestock('');
              } else {
                setStatus('Failed to update low flag');
              }
            } catch (err) {
              setStatus('Error: ' + err.message);
            }
          };
          actions.appendChild(lowToggle);
        }
        d.appendChild(actions);
        
        container.appendChild(d);
      });
    }
  }
}

async function adjustItemQuantity(itemId, delta) {
  try {
    const resp = await fetch(`/items/${itemId}/adjust`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ delta })
    });
    if (resp.ok) {
      setStatus('Quantity updated');
      loadItems();
      handleRestock('');
    } else {
      setStatus('Failed to adjust quantity');
    }
  } catch (err) {
    setStatus('Error: ' + err.message);
  }
}

async function setItemQuantity(itemId, currentQty) {
  const newQty = prompt('Set on-hand quantity:', currentQty);
  if (newQty === null) return;
  const qty = parseInt(newQty, 10);
  if (isNaN(qty) || qty < 0) {
    alert('Please enter a valid number');
    return;
  }
  
  try {
    const resp = await fetch(`/items/${itemId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ on_hand: qty })
    });
    if (resp.ok) {
      setStatus('Quantity set');
      loadItems();
      handleRestock('');
    } else {
      setStatus('Failed to set quantity');
    }
  } catch (err) {
    setStatus('Error: ' + err.message);
  }
}

async function deleteItem(itemId) {
  if (!confirm('Delete this item?')) return;
  try {
    const resp = await fetch(`/items/${itemId}`, { method: 'DELETE' });
    if (resp.ok) {
      setStatus('Item deleted');
      loadItems();
      handleRestock('');
    } else {
      setStatus('Failed to delete item');
    }
  } catch (err) {
    setStatus('Error: ' + err.message);
  }
}

// Form handlers
function setupForms() {
  const vendorForm = document.getElementById('vendor-form');
  if (vendorForm) {
    vendorForm.onsubmit = async (e) => {
      e.preventDefault();
      const name = document.getElementById('vendor-name').value.trim();
      if (!name) return;
      
      try {
        const resp = await fetch('/vendors', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name })
        });
        if (resp.ok) {
          setStatus('Vendor added');
          vendorForm.reset();
          loadVendors();
        } else {
          const err = await resp.json();
          setStatus('Error: ' + (err.error || 'Failed'));
        }
      } catch (err) {
        setStatus('Error: ' + err.message);
      }
    };
  }
  
  const areaForm = document.getElementById('area-form');
  if (areaForm) {
    areaForm.onsubmit = async (e) => {
      e.preventDefault();
      const name = document.getElementById('area-name').value.trim();
      const vendor_id = document.getElementById('area-vendor').value || null;
      if (!name) return;
      
      try {
        const resp = await fetch('/storage-areas', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, vendor_id })
        });
        if (resp.ok) {
          setStatus('Storage area added');
          areaForm.reset();
          loadStorageAreas();
        } else {
          const err = await resp.json();
          setStatus('Error: ' + (err.error || 'Failed'));
        }
      } catch (err) {
        setStatus('Error: ' + err.message);
      }
    };
  }
  
  const itemForm = document.getElementById('item-form');
  if (itemForm) {
    itemForm.onsubmit = async (e) => {
      e.preventDefault();
      const name = document.getElementById('item-name').value.trim();
      const storage_area_id = parseInt(document.getElementById('item-storage-area').value, 10);
      const vendor_id = document.getElementById('item-vendor').value || null;
      const minimum_quantity = parseInt(document.getElementById('item-minimum').value, 10);
      const on_hand = parseInt(document.getElementById('item-on-hand').value, 10);
      const tracking_method = document.getElementById('item-tracking') ? document.getElementById('item-tracking').value : 'quantity';
      const is_low = document.getElementById('item-is-low') ? document.getElementById('item-is-low').checked : false;

      if (!name || !storage_area_id) return;

      try {
        const resp = await fetch('/items', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, storage_area_id, vendor_id, minimum_quantity, on_hand, tracking_method, is_low })
        });
        if (resp.ok) {
          setStatus('Item added');
          itemForm.reset();
          loadItems();
          handleRestock('');
        } else {
          const err = await resp.json();
          setStatus('Error: ' + (err.error || 'Failed'));
        }
      } catch (err) {
        setStatus('Error: ' + err.message);
      }
    };
  }
  
  const manualRestockForm = document.getElementById('manual-restock-form');
  if (manualRestockForm) {
    manualRestockForm.onsubmit = async (e) => {
      e.preventDefault();
      const name = document.getElementById('manual-name').value.trim();
      const vendor_id = document.getElementById('manual-vendor').value || null;
      const storage_area_id = document.getElementById('manual-storage-area').value || null;
      const reason = document.getElementById('manual-reason').value.trim() || null;
      
      if (!name) return;
      
      try {
        const resp = await fetch('/restock/manual', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, vendor_id, storage_area_id, reason })
        });
        if (resp.ok) {
          setStatus('Manual entry added');
          manualRestockForm.reset();
          handleRestock('');
        } else {
          const err = await resp.json();
          setStatus('Error: ' + (err.error || 'Failed'));
        }
      } catch (err) {
        setStatus('Error: ' + err.message);
      }
    };
  }
}

// Page initialization
window.addEventListener('load', () => {
  const path = window.location.pathname;
  
  setupForms();
  
  if (path === '/' ) {
    handleRestock('');
  } else if (path.startsWith('/restock-ui')) {
    loadVendors().then(() => loadStorageAreas()).then(() => handleRestock(''));
  } else if (path.startsWith('/storage-areas-ui')) {
    loadVendors().then(() => loadStorageAreas());
  } else if (path.startsWith('/items-ui')) {
    loadVendors().then(() => loadStorageAreas()).then(() => loadItems());
  } else if (path.startsWith('/vendors-ui')) {
    loadVendors();
  }
});
