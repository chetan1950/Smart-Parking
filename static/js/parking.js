(() => {
  const root = document.getElementById('parking-editor');
  if (!root) return;
  const image = document.getElementById('reference-image');
  const canvas = document.getElementById('parking-canvas');
  const context = canvas.getContext('2d');
  const list = document.getElementById('space-list');
  const hint = document.getElementById('editor-hint');
  let spaces = (window.PARKING_LAYOUT.ids || []).map((id, index) => ({ id, points: window.PARKING_LAYOUT.spaces[index] || [] }));
  let draft = null;

  function scale() { return { x: canvas.width / image.naturalWidth, y: canvas.height / image.naturalHeight }; }
  function drawPolygon(points, color, label) {
    if (!points.length) return;
    const factor = scale();
    context.beginPath();
    points.forEach((p, i) => { const x = p[0] * factor.x, y = p[1] * factor.y; i ? context.lineTo(x, y) : context.moveTo(x, y); });
    if (points.length > 2) context.closePath();
    context.strokeStyle = color; context.lineWidth = 3; context.stroke();
    points.forEach(([x, y]) => { context.fillStyle = color; context.beginPath(); context.arc(x * factor.x, y * factor.y, 4, 0, Math.PI * 2); context.fill(); });
    context.fillStyle = color; context.font = '600 14px DM Sans'; context.fillText(label, points[0][0] * factor.x + 6, points[0][1] * factor.y - 6);
  }
  function render() {
    canvas.width = image.clientWidth; canvas.height = image.clientHeight; context.clearRect(0, 0, canvas.width, canvas.height);
    spaces.forEach(space => drawPolygon(space.points, '#67d68b', space.id));
    if (draft) drawPolygon(draft.points, '#f5bd51', `${draft.id} (drawing)`);
    list.innerHTML = '';
    spaces.forEach((space, index) => { const li = document.createElement('li'); li.innerHTML = `<input aria-label="Space ID" value="${space.id}"><span>${space.points.length} points</span><button type="button" aria-label="Delete ${space.id}">×</button>`;
      const input = li.querySelector('input'); input.addEventListener('change', () => { const id = input.value.trim().toUpperCase(); if (!id || spaces.some((other, i) => i !== index && other.id === id)) { input.value = space.id; return; } space.id = id; render(); });
      li.querySelector('button').addEventListener('click', () => { spaces.splice(index, 1); render(); }); list.appendChild(li); });
  }
  function resize() { if (image.naturalWidth) render(); }
  image.addEventListener('load', resize); window.addEventListener('resize', resize);
  canvas.addEventListener('click', (event) => { if (!draft) return; const rect = canvas.getBoundingClientRect(); const x = (event.clientX - rect.left) * image.naturalWidth / rect.width; const y = (event.clientY - rect.top) * image.naturalHeight / rect.height; draft.points.push([Math.round(x * 100) / 100, Math.round(y * 100) / 100]); hint.textContent = `${draft.points.length} point(s) selected for ${draft.id}. Use Finish polygon when ready.`; render(); });
  document.getElementById('new-space').addEventListener('click', () => { if (draft) return; const id = window.prompt('Parking space ID:', `P${String(spaces.length + 1).padStart(3, '0')}`)?.trim().toUpperCase(); if (!id || spaces.some(space => space.id === id)) return; draft = { id, points: [] }; hint.textContent = `Drawing ${id}: click at least three corners.`; render(); });
  document.getElementById('finish-space').addEventListener('click', () => { if (!draft) return; if (draft.points.length < 3) { hint.textContent = 'A parking region requires at least three points.'; return; } spaces.push(draft); draft = null; hint.textContent = 'Space added. Add another or save the layout.'; render(); });
  document.getElementById('reset-layout').addEventListener('click', () => { if (window.confirm('Remove all unsaved parking spaces?')) { spaces = []; draft = null; hint.textContent = 'Layout reset. Add a parking space to begin.'; render(); } });
  document.getElementById('save-layout').addEventListener('click', async () => { if (draft) { hint.textContent = 'Finish or discard the current polygon before saving.'; return; } const button = document.getElementById('save-layout'); button.disabled = true; try { const response = await fetch('/parking-layout/save', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ configuration_id: Number(root.dataset.configurationId), spaces }) }); const data = await response.json(); if (!response.ok) throw new Error(data.error || 'Could not save layout.'); hint.textContent = `${data.message} ${data.space_count} spaces saved.`; } catch (error) { hint.textContent = error.message; } finally { button.disabled = false; } });
  resize();
})();
