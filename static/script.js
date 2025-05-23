const apiUrl = '/api/tracks';

let currentPage = 1;
const perPage = 20;

async function fetchTracks(page = 1) {
  const res = await fetch(`${apiUrl}?page=${page}&per_page=${perPage}`);
  return res.json();
}

function createCell(text) {
  const td = document.createElement('td');
  td.textContent = text;
  return td;
}

function createEditableCell(text, field) {
  const td = document.createElement('td');
  td.textContent = text;
  td.setAttribute('data-field', field);
  return td;
}

function createRatingCell(track) {
  const td = document.createElement('td');
  const emojis = ['😍', '🙂', '😐', '😞'];

  emojis.forEach(e => {
    const btn = document.createElement('span');
    btn.textContent = e;
    btn.className = 'emoji-btn';
    btn.setAttribute('data-bs-toggle', 'tooltip');
    btn.setAttribute('title', `Rate ${e}`);
    btn.addEventListener('click', async () => {
      await rateTrack(track.id, e);
      showAlert(`Rated track with ${e}`, 'info');
    });
    td.appendChild(btn);
  });

  const ratingDisplay = document.createElement('span');
  ratingDisplay.className = 'rating';
  ratingDisplay.textContent = track.rating || '';
  td.appendChild(ratingDisplay);
  return td;
}

function createPlayCell(previewUrl) {
  const td = document.createElement('td');
  if (!previewUrl) {
    td.textContent = 'No preview';
    td.classList.add('text-muted');
    return td;
  }

  const audio = document.createElement('audio');
  audio.src = previewUrl;
  audio.preload = 'none';

  const btn = document.createElement('button');
  btn.className = 'btn btn-outline-success btn-sm';
  btn.textContent = 'Play';
  btn.onclick = () => {
    if (audio.paused) {
      audio.play();
      btn.textContent = 'Pause';
    } else {
      audio.pause();
      btn.textContent = 'Play';
    }
  };

  audio.onended = () => {
    btn.textContent = 'Play';
  };

  td.appendChild(btn);
  td.appendChild(audio);
  return td;
}

function createEditCell(track) {
  const td = document.createElement('td');
  const editBtn = document.createElement('button');
  editBtn.className = 'btn btn-primary btn-sm';
  editBtn.textContent = 'Edit';

  let editing = false;
  let editableCells = [];

  editBtn.onclick = () => {
    if (!editing) {
      // Enable editing on editable cells
      editableCells = [];
      ['track_name', 'artist_name', 'album_name', 'preview_url'].forEach(field => {
        const cell = td.parentElement.querySelector(`td[data-field=${field}]`);
        if (cell) {
          cell.contentEditable = true;
          cell.classList.add('editable');
          editableCells.push(cell);
        }
      });
      editBtn.textContent = 'Save';
      editing = true;
    } else {
      // Save edits
      const updatedData = {};
      editableCells.forEach(cell => {
        cell.contentEditable = false;
        cell.classList.remove('editable');
        updatedData[cell.getAttribute('data-field')] = cell.textContent.trim();
      });

      fetch(`${apiUrl}/${track.id}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(updatedData)
      }).then(() => {
        showAlert('Track updated successfully!', 'success');
        editBtn.textContent = 'Edit';
        editing = false;
        // Reload table to update preview button if URL changed
        loadTable(currentPage);
      }).catch(() => {
        showAlert('Failed to update track.', 'danger');
      });
    }
  };

  td.appendChild(editBtn);
  return td;
}

async function rateTrack(id, emoji) {
  await fetch(`${apiUrl}/${id}/rating`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({emoji})
  });
  await loadTable(currentPage);
}

async function deleteTrack(id) {
  if (!confirm('Are you sure you want to delete this track?')) return;
  await fetch(`${apiUrl}/${id}`, { method: 'DELETE' });
  showAlert('Track deleted successfully!', 'warning');
  await loadTable(currentPage);
}

function buildPagination(paginationData) {
  const pagination = document.getElementById('pagination');
  pagination.innerHTML = '';

  const prevLi = document.createElement('li');
  prevLi.className = `page-item ${paginationData.has_prev ? '' : 'disabled'}`;
  const prevLink = document.createElement('a');
  prevLink.className = 'page-link';
  prevLink.href = '#';
  prevLink.textContent = 'Previous';
  prevLink.onclick = e => {
    e.preventDefault();
    if (paginationData.has_prev) {
      currentPage = paginationData.page - 1;
      loadTable(currentPage);
    }
  };
  prevLi.appendChild(prevLink);
  pagination.appendChild(prevLi);

  const totalPages = paginationData.pages;
  const current = paginationData.page;
  const startPage = Math.max(1, current - 2);
  const endPage = Math.min(totalPages, current + 2);

  for (let i = startPage; i <= endPage; i++) {
    const li = document.createElement('li');
    li.className = `page-item ${i === current ? 'active' : ''}`;
    const a = document.createElement('a');
    a.className = 'page-link';
    a.href = '#';
    a.textContent = i;
    a.onclick = e => {
      e.preventDefault();
      currentPage = i;
      loadTable(currentPage);
    };
    li.appendChild(a);
    pagination.appendChild(li);
  }

  const nextLi = document.createElement('li');
  nextLi.className = `page-item ${paginationData.has_next ? '' : 'disabled'}`;
  const nextLink = document.createElement('a');
  nextLink.className = 'page-link';
  nextLink.href = '#';
  nextLink.textContent = 'Next';
  nextLink.onclick = e => {
    e.preventDefault();
    if (paginationData.has_next) {
      currentPage = paginationData.page + 1;
      loadTable(currentPage);
    }
  };
  nextLi.appendChild(nextLink);
  pagination.appendChild(nextLi);
}

async function loadTable(page = 1) {
  const data = await fetchTracks(page);
  const tbody = document.querySelector('#tracks-table tbody');
  tbody.innerHTML = '';

  data.tracks.forEach(track => {
    const tr = document.createElement('tr');

    tr.appendChild(createCell(track.id));

    tr.appendChild(createEditableCell(track.track_name, 'track_name'));
    tr.appendChild(createEditableCell(track.artist_name, 'artist_name'));
    tr.appendChild(createEditableCell(track.album_name || '', 'album_name'));
    tr.appendChild(createRatingCell(track));
    tr.appendChild(createPlayCell(track.preview_url || ''));
    tr.appendChild(createEditCell(track));

    const actionTd = document.createElement('td');
    const delBtn = document.createElement('button');
    delBtn.className = 'btn btn-danger btn-sm';
    delBtn.innerHTML = '<i class="bi bi-trash"></i>';
    delBtn.title = 'Delete Track';
    delBtn.onclick = () => deleteTrack(track.id);
    actionTd.appendChild(delBtn);
    tr.appendChild(actionTd);

    tbody.appendChild(tr);
  });

  buildPagination(data);

  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

function showAlert(message, type = 'info') {
  const alertPlaceholder = document.getElementById('alert-placeholder');
  const wrapper = document.createElement('div');
  wrapper.innerHTML = `
    <div class="alert alert-${type} alert-dismissible fade show" role="alert">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
  `;
  alertPlaceholder.append(wrapper);

  setTimeout(() => {
    bootstrap.Alert.getOrCreateInstance(wrapper.querySelector('.alert')).close();
  }, 3500);
}

// Bootstrap form validation and submit
(() => {
  'use strict';
  const forms = document.querySelectorAll('.needs-validation');
  Array.from(forms).forEach(form => {
    form.addEventListener('submit', async event => {
      event.preventDefault();
      event.stopPropagation();
      if (!form.checkValidity()) {
        form.classList.add('was-validated');
        return;
      }
      const formData = new FormData(form);
      const newTrack = {
        track_name: formData.get('track_name').trim(),
        artist_name: formData.get('artist_name').trim(),
        album_name: formData.get('album_name').trim(),
        preview_url: formData.get('preview_url').trim()
      };
      await fetch(apiUrl, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(newTrack)
      });
      form.reset();
      form.classList.remove('was-validated');
      showAlert('Track added successfully!', 'success');
      loadTable(currentPage);
    }, false);
  });
})();

loadTable(currentPage);
