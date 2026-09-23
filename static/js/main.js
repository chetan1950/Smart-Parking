document.querySelector('.nav-toggle')?.addEventListener('click', () => document.querySelector('.topbar nav')?.classList.toggle('open'));

document.querySelectorAll('.upload-form').forEach((form) => {
  const input = form.querySelector('input[type="file"]');
  const filename = form.querySelector('.file-name');
  input?.addEventListener('change', () => {
    const file = input.files?.[0];
    filename.textContent = file ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(2)} MB` : 'No file selected';
  });
  form.addEventListener('submit', () => {
    const button = form.querySelector('button[type="submit"]');
    if (button) { button.disabled = true; button.textContent = form.dataset.videoForm !== undefined ? 'Processing frames…' : 'Running YOLO…'; }
  });
});
