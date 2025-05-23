const form = document.getElementById('track-form');
const message = document.getElementById('message');
const tableBody = document.getElementById('tracks-table-body');
const submitBtn = document.getElementById('submit-btn');
const searchInput = document.getElementById('search-input');
const sortSelect = document.getElementById('sort-select');
const paginationDiv = document.getElementById('pagination');

let editingId = null;
let topArtistsChartInstance = null;
let genreChartInstance = null;

let currentPage = 1;
let totalPages = 1;
const perPage = 10;

async function fetchTracks(page = 1) {
  const search = searchInput.value.trim();
  const sort = sortSelect.value;

  const params = new URLSearchParams({
    page,
    per_page: perPage,
    sort,
  });
  if (search) params.append('search', search);

  try {
    const res = await fetch(`/api/tracks?${params.toString()}`);
    if (!res.ok) throw new Error('Failed to load tracks.');
    const data = await res.json();
    renderTable(data.tracks);
    setupPagination(data.page, data.pages);
  } catch (err) {
    message.style.color = 'red';
    message.textContent = err.message;
  }
}

function renderTable(tracks) {
  tableBody.innerHTML = '';
  tracks.forEach(t => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${t.id}</td>
      <td>${t.track_name}</td>
      <td>${t.artist}</td>
      <td>${t.album || ''}</td>
      <td>${t.release_date || ''}</td>
      <td>${t.popularity ?? ''}</td>
      <td>${t.spotify_url ? `<a href="${t.spotify_url}" target="_blank" rel="noopener">Link</a>` : ''}</td>
      <td>${t.duration_min ?? ''}</td>
      <td>${t.genre || ''}</td>
      <td>
        <button class="btn btn-edit" aria-label="Edit track ${t.track_name}">Edit</button>
        <button class="btn btn-delete" aria-label="Delete track ${t.track_name}">Delete</button>
      </td>
    `;
    tr.querySelector('.btn-edit').addEventListener('click', () => fillForm(t));
    tr.querySelector('.btn-delete').addEventListener('click', () => deleteTrack(t.id));
    tableBody.appendChild(tr);
  });
}

function fillForm(track) {
  editingId = track.id;
  form['track-id'].value = track.id;
  form['track-id'].disabled = true;
  form['track-name'].value = track.track_name;
  form['artist'].value = track.artist;
  form['album'].value = track.album || '';
  form['release-date'].value = track.release_date || '';
  form['popularity'].value = track.popularity ?? '';
  form['spotify-url'].value = track.spotify_url || '';
  form['duration-min'].value = track.duration_min ?? '';
  form['genre'].value = track.genre || '';
  submitBtn.textContent = 'Update Track';
  message.textContent = '';
}

function clearForm() {
  editingId = null;
  form.reset();
  form['track-id'].disabled = false;
  submitBtn.textContent = 'Add Track';
  message.textContent = '';
}

async function deleteTrack(id) {
  if (!confirm('Are you sure you want to delete this track?')) return;
  try {
    const res = await fetch(`/api/tracks/${id}`, { method: 'DELETE' });
    if (!res.ok) throw new Error();
    message.style.color = 'green';
    message.textContent = 'Track deleted successfully!';
    clearForm();
    fetchTracks(currentPage);
    drawTopArtistsChart();
    drawGenreChart();
  } catch {
    message.style.color = 'red';
    message.textContent = 'Failed to delete track.';
  }
}

form.addEventListener('submit', async e => {
  e.preventDefault();
  const trackData = {
    id: form['track-id'].value.trim(),
    track_name: form['track-name'].value.trim(),
    artist: form['artist'].value.trim(),
    album: form['album'].value.trim(),
    release_date: form['release-date'].value.trim(),
    popularity: parseInt(form['popularity'].value) || 0,
    spotify_url: form['spotify-url'].value.trim(),
    duration_min: parseFloat(form['duration-min'].value) || 0,
    genre: form['genre'].value.trim()
  };
  try {
    let res;
    if (editingId) {
      res = await fetch(`/api/tracks/${editingId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trackData)
      });
    } else {
      res = await fetch('/api/tracks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trackData)
      });
    }
    if (!res.ok) {
      const error = await res.json();
      throw new Error(error.error || 'Failed to save track.');
    }
    message.style.color = 'green';
    message.textContent = editingId ? 'Track updated successfully!' : 'Track added successfully!';
    clearForm();



