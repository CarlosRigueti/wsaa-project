async function fetchTracks() {
    const res = await fetch('/api/tracks');
    const tracks = await res.json();
    const list = document.getElementById('track-list');
    list.innerHTML = '';

    tracks.forEach(track => {
        const li = document.createElement('li');
        li.innerHTML = `
            <strong>${track.track_name}</strong> by ${track.artist} 
            [Album: ${track.album || '-'}] 
            [Released: ${track.release_date || '-'}] 
            [Popularity: ${track.popularity || '-'}] 
            [Duration: ${track.duration_min ? track.duration_min.toFixed(2) : '-'} min]
            <a href="${track.spotify_url}" target="_blank">Spotify Link</a>
            <button onclick="deleteTrack('${track.id}')">Delete</button>
        `;
        list.appendChild(li);
    });
}

async function deleteTrack(id) {
    await fetch(`/api/tracks/${id}`, { method: 'DELETE' });
    fetchTracks();
}

document.getElementById('track-form').addEventListener('submit', async e => {
    e.preventDefault();

    const data = {
        id: document.getElementById('id').value.trim(),
        track_name: document.getElementById('track_name').value.trim(),
        artist: document.getElementById('artist').value.trim(),
        album: document.getElementById('album').value.trim(),
        release_date: document.getElementById('release_date').value.trim(),
        popularity: Number(document.getElementById('popularity').value),
        spotify_url: document.getElementById('spotify_url').value.trim(),
        duration_min: parseFloat(document.getElementById('duration_min').value),
    };

    // Verifica se a track já existe
    const existingTracks = await fetch('/api/tracks').then(r => r.json());
    const exists = existingTracks.some(t => t.id === data.id);

    if (exists) {
        await fetch(`/api/tracks/${data.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
    } else {
        await fetch('/api/tracks', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
    }

    e.target.reset();
    fetchTracks();
});

fetchTracks();
