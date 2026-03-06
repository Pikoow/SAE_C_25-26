// Configuration
const API_BASE_URL = "http://127.0.0.1:8000";
const AUTH_API_URL = "http://localhost:3000";
let currentUserId = null;
let selectedTracks = [];

// Initialisation
$(document).ready(function () {
    checkAuthenticatedUser();
    setupTrackSearch();
    setupCreateModal();
    $("#create-playlist-button").on("click", createPlaylist);
    $("#generate-playlist-btn").on("click", generateAutoPlaylist);

    // Gestionnaire pour le bouton principal "Créer une playlist"
    $("#open-create-playlist-btn").on("click", openCreateModal);

    // Initialiser la gestion de la modal de création
    setupCreateModal();
});

// ===== GESTION DE LA MODAL DE CRÉATION =====
function setupCreateModal() {
    $("#close-create-modal").on("click", closeCreateModal);

    $("#create-playlist-modal").on("click", function(e) {
        if ($(e.target).is("#create-playlist-modal")) {
            closeCreateModal();
        }
    });

    $(document).on("keydown", function(e) {
        if (e.key === "Escape" && $("#create-playlist-modal").is(":visible")) {
            closeCreateModal();
        }
    });
}

// FIX : fadeIn() pose display:block, pas flex → le contenu n'est pas centré.
// On force display:flex AVANT le fadeIn pour que le centrage fonctionne.
function openCreateModal() {
    $("#create-playlist-modal")
        .css("display", "flex")   // force flex pour centrer le contenu
        .hide()                   // repasse à none instantanément (sans transition)
        .fadeIn(200);             // anime opacity 0 → 1 en partant de flex
    $("body").css("overflow", "hidden");
    setTimeout(() => $("#playlist-name-input").focus(), 250);
}

function closeCreateModal() {
    $("#create-playlist-modal").fadeOut(200, function () {
        $(this).css("display", "none"); // nettoyage explicite après l'animation
    });
    $("body").css("overflow", "");
}

// ===== AUTHENTIFICATION =====
async function checkAuthenticatedUser() {
    try {
        const response = await fetch(`${AUTH_API_URL}/dashboard`, {
            method: "GET",
            credentials: "include"
        });

        const data = await response.json();

        if (!data.error) {
            currentUserId = data.user.user_id || 1;
            loadUserPlaylists(currentUserId);
        }
    } catch (err) {
        console.error("Erreur d'authentification:", err);
        currentUserId = 1;
        loadUserPlaylists(currentUserId);
    }
}

// ===== CHARGEMENT DES PLAYLISTS =====
async function loadUserPlaylists(userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}/playlists/detailed`);
        const data = await response.json();
        displayPlaylists(data.playlists || []);
    } catch (error) {
        console.error("Erreur lors du chargement des playlists:", error);
        showNotification("Erreur lors du chargement des playlists", "error");
    }
}

// ===== AFFICHAGE DES PLAYLISTS =====
function displayPlaylists(playlists) {
    const container = $(".playlists-container");
    container.empty();

    if (playlists.length === 0) {
        container.html(`
            <div class="empty-state">
                <p>Vous n'avez pas encore de playlist</p>
                <p>Créez votre première playlist en cliquant sur la carte ci-contre !</p>
            </div>
        `);
    } else {
        playlists.forEach(playlist => {
            const playlistCard = createPlaylistCard(playlist);
            container.append(playlistCard);
        });
    }

    // Toujours ajouter la carte "+" en dernier
    appendNewPlaylistCard(container);
}

// Ajouter la carte "+ Nouvelle playlist"
function appendNewPlaylistCard(container) {
    const newCard = $(`
        <div class="playlist-card-new" id="open-create-playlist" title="Créer une nouvelle playlist">
            <div class="new-playlist-plus">+</div>
            <span class="new-playlist-label">Nouvelle playlist</span>
        </div>
    `);

    newCard.on("click", openCreateModal);
    container.append(newCard);
}

// ===== CARTE DE PLAYLIST =====
function createPlaylistCard(playlist) {
    const card = $(`
        <div class="playlist-card" data-playlist-id="${playlist.playlist_id}">
            <div class="playlist-cover-grid">
                ${generatePlaylistCovers(playlist.preview_tracks || [])}
            </div>
            <div class="playlist-info">
                <h3>${escapeHtml(playlist.playlist_name)}</h3>
                <p class="playlist-description">${escapeHtml(playlist.playlist_description || "Aucune description")}</p>
                <div class="playlist-meta">
                    <span>${playlist.tracks_count || 0} titre(s)</span>
                    <span>Créée le ${formatDate(playlist.created_at)}</span>
                </div>
                <div class="playlist-actions">
                    <button class="btn-delete pl-delete-btn" data-pid="${playlist.playlist_id}">
                        Supprimer
                    </button>
                </div>
            </div>
        </div>
    `);

    card.css("cursor", "pointer");
    card.on("click", function () {
        viewPlaylist(playlist.playlist_id);
    });

    card.find(".pl-delete-btn").on("click", function (e) {
        e.stopPropagation();
        deletePlaylist($(this).data("pid"));
    });

    return card;
}

// ===== GÉNÉRATION AUTO =====
async function generateAutoPlaylist() {
    if (!currentUserId) {
        showNotification("Veuillez vous connecter pour générer une playlist.", "error");
        return;
    }

    try {
        showNotification("Génération de votre playlist personnalisée...", "info");

        const favResponse = await fetch(`${API_BASE_URL}/voir_favorite/${currentUserId}`);
        const favData = await favResponse.json();

        if (!favData.results || favData.results.length === 0) {
            showNotification("Ajoutez des favoris depuis la page préférences pour générer une playlist !", "warning");
            return;
        }

        const favorites = favData.results[0];
        const trackSeeds = favorites.ids_tracks ? favorites.ids_tracks.split(',').filter(id => id) : [];
        const artistSeeds = favorites.ids_artists ? favorites.ids_artists.split(',').filter(id => id) : [];

        let generatedTrackIds = new Set();

        if (trackSeeds.length > 0) {
            const trackParams = trackSeeds.map(id => `track_ids=${id}`).join('&');
            const recTracksResp = await fetch(`${API_BASE_URL}/reco/tracks?${trackParams}&limit=15`);
            const recTracksData = await recTracksResp.json();
            if (recTracksData.results) {
                recTracksData.results.forEach(t => generatedTrackIds.add(t.track_id));
            }
        }

        if (artistSeeds.length > 0) {
            const artistParams = artistSeeds.map(id => `artist_ids=${id}`).join('&');
            const recArtistsResp = await fetch(`${API_BASE_URL}/reco/artists?${artistParams}&limit=5`);
            const recArtistsData = await recArtistsResp.json();

            if (recArtistsData.results) {
                for (const artist of recArtistsData.results) {
                    const artistTracksResp = await fetch(`${API_BASE_URL}/artists/${artist.artist_id}/tracks?limit=3`);
                    const artistTracksData = await artistTracksResp.json();
                    if (artistTracksData.tracks) {
                        artistTracksData.tracks.forEach(t => generatedTrackIds.add(t.track_id));
                    }
                }
            }
        }

        let finalTrackList = Array.from(generatedTrackIds);
        const size = 10;
        finalTrackList = finalTrackList.sort(() => 0.5 - Math.random()).slice(0, size);

        if (finalTrackList.length === 0) {
            showNotification("Pas assez de recommandations trouvées.", "warning");
            return;
        }

        const playlistPayload = {
            name: `Playlist Générée`,
            description: `Générée automatiquement le ${new Date().toLocaleDateString('fr-FR')}.`,
            user_id: parseInt(currentUserId),
            track_ids: finalTrackList.map(id => parseInt(id))
        };

        const createResp = await fetch(`${API_BASE_URL}/playlists`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(playlistPayload)
        });

        if (createResp.ok) {
            showNotification("Playlist générée avec succès !", "success");
            loadUserPlaylists(currentUserId);
        } else {
            const error = await createResp.json();
            throw new Error(error.detail || "Erreur lors de la création");
        }

    } catch (err) {
        console.error("Erreur generation playlist:", err);
        showNotification("Erreur lors de la génération : " + err.message, "error");
    }
}

// ===== COVERS =====
function generatePlaylistCovers(tracks) {
    if (tracks.length === 0) {
        return `<div class="no-cover">🎵</div>`;
    }

    let html = '<div class="cover-grid">';
    tracks.slice(0, 4).forEach(track => {
        let imageUrl = getTrackImageUrl(track);
        html += `<div class="cover-item">
            <img src="${imageUrl}" alt="${escapeHtml(track.track_title)}" onerror="this.src='images/no_image_music.avif'">
        </div>`;
    });

    for (let i = tracks.length; i < 4; i++) {
        html += `<div class="cover-item">
            <img src="images/no_image_music.avif" alt="Aucune image">
        </div>`;
    }

    html += '</div>';
    return html;
}

function getTrackImageUrl(track) {
    if (track.track_image_file) {
        const match = track.track_image_file.match(/([^/]+\.(jpg|png|jpeg))$/i);
        const filename = match ? match[1] : track.track_image_file;
        if (filename) {
            return `https://freemusicarchive.org/image/?file=images%2Falbums%2F${filename}&width=290&height=290&type=album`;
        }
    }
    return 'images/no_image_music.avif';
}

// ===== RECHERCHE DE TRACKS (AUTOCOMPLETE) =====
function setupTrackSearch() {
    const searchInput = $("#track-search-input");

    searchInput.autocomplete({
        source: async function (request, response) {
            try {
                const result = await fetch(`${API_BASE_URL}/search/tracks?query=${encodeURIComponent(request.term)}&limit=8`);
                const data = await result.json();

                const suggestions = data.results.map(track => ({
                    label: `${track.track_title} - ${track.artist_names || "Artiste inconnu"}`,
                    value: track.track_title,
                    id: track.track_id,
                    artist: track.artist_names,
                    image: getTrackImageUrl(track)
                }));

                response(suggestions);
            } catch (error) {
                console.error("Erreur de recherche:", error);
                response([]);
            }
        },
        minLength: 2,
        select: function (event, ui) {
            addTrackToSelection(ui.item.id, ui.item.label, ui.item.image);
            $(this).val("");
            return false;
        }
    }).autocomplete("instance")._renderItem = function (ul, item) {
        return $(`<li>`)
            .append(`
                <div class="search-result-item">
                    <img src="${item.image}" alt="" class="search-result-image">
                    <div class="search-result-info">
                        <div class="search-result-title">${item.label}</div>
                        <div class="search-result-artist">${item.artist || "Artiste inconnu"}</div>
                    </div>
                </div>
            `)
            .appendTo(ul);
    };
}

// ===== SÉLECTION DES TRACKS =====
function addTrackToSelection(trackId, trackTitle, imageUrl) {
    if (selectedTracks.some(t => t.id === trackId)) {
        showNotification("Cette musique est déjà dans la sélection", "info");
        return;
    }

    selectedTracks.push({ id: trackId, title: trackTitle, image: imageUrl });
    updateSelectedCount();
    displaySelectedTracks();
}

function updateSelectedCount() {
    $("#selected-count").text(`(${selectedTracks.length})`);
}

function displaySelectedTracks() {
    const container = $("#selected-tracks-container");
    container.empty();

    if (selectedTracks.length === 0) {
        container.html('<p class="no-selection">Aucune musique sélectionnée</p>');
        return;
    }

    selectedTracks.forEach((track) => {
        const badge = $(`
            <div class="selected-track-badge" data-track-id="${track.id}">
                <img src="${track.image}" alt="" class="track-mini-image">
                <span class="track-name">${escapeHtml(track.title)}</span>
                <span class="remove-track" onclick="removeTrackFromSelection(${track.id})">✕</span>
            </div>
        `);
        container.append(badge);
    });
}

window.removeTrackFromSelection = function (trackId) {
    selectedTracks = selectedTracks.filter(t => t.id !== trackId);
    updateSelectedCount();
    displaySelectedTracks();
};

// ===== CRÉATION DE PLAYLIST =====
async function createPlaylist() {
    const name = $("#playlist-name-input").val().trim();
    const description = $("#playlist-description-input").val().trim();

    if (!name) {
        showNotification("Veuillez donner un nom à votre playlist", "warning");
        return;
    }

    if (!currentUserId) {
        showNotification("Vous devez être connecté pour créer une playlist", "error");
        return;
    }

    const trackIds = selectedTracks.map(t => t.id);

    try {
        const response = await fetch(`${API_BASE_URL}/playlists`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: name,
                description: description,
                user_id: currentUserId,
                track_ids: trackIds
            })
        });

        if (response.ok) {
            showNotification("Playlist créée avec succès !", "success");
            $("#playlist-name-input").val("");
            $("#playlist-description-input").val("");
            selectedTracks = [];
            updateSelectedCount();
            displaySelectedTracks();
            closeCreateModal();
            loadUserPlaylists(currentUserId);
        } else {
            showNotification("Erreur lors de la création", "error");
        }
    } catch (error) {
        console.error("Erreur:", error);
        showNotification("Erreur lors de la création de la playlist", "error");
    }
}

// ===== VOIR / SUPPRIMER PLAYLIST =====
window.viewPlaylist = function (playlistId) {
    fetch(`${API_BASE_URL}/playlists/${playlistId}`)
        .then(response => response.json())
        .then(playlist => {
            showPlaylistModal(playlist);
        })
        .catch(error => {
            console.error("Erreur:", error);
            showNotification("Erreur lors du chargement de la playlist", "error");
        });
};

window.deletePlaylist = async function (playlistId) {
    if (!confirm("Êtes-vous sûr de vouloir supprimer cette playlist ?")) return;

    try {
        const response = await fetch(`${API_BASE_URL}/playlists/${playlistId}`, { method: "DELETE" });

        if (response.ok) {
            showNotification("Playlist supprimée avec succès", "success");
            loadUserPlaylists(currentUserId);
        } else {
            showNotification("Erreur lors de la suppression", "error");
        }
    } catch (error) {
        console.error("Erreur:", error);
        showNotification("Erreur lors de la suppression", "error");
    }
};

// ===== MODAL DE DÉTAIL PLAYLIST =====
function showPlaylistModal(playlist) {
    $("#playlist-modal").remove();

    const tracks = playlist.tracks || [];
    const tracksCount = tracks.length;

    let coverGridHtml = '';
    for (let i = 0; i < 4; i++) {
        const imgUrl = tracks[i] ? getTrackImageUrl(tracks[i]) : 'images/no_image_music.avif';
        coverGridHtml += `<img src="${imgUrl}" alt="" onerror="this.src='images/no_image_music.avif'">`;
    }

    let tracksHtml = '';
    if (tracksCount > 0) {
        tracks.forEach((track, idx) => {
            const mins = Math.floor((track.track_duration || 0) / 60);
            const secs = (track.track_duration || 0) % 60;
            const dur = `${mins}:${secs.toString().padStart(2, '0')}`;

            tracksHtml += `
                <div class="modal-track-item" data-track-id="${track.track_id}" data-index="${idx}">
                    <div class="pl-track-num">
                        <span class="pl-num-text">${idx + 1}</span>
                        <span class="pl-play-icon">
                            <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                        </span>
                    </div>
                    <img src="${getTrackImageUrl(track)}" alt="" class="track-image" onerror="this.src='images/no_image_music.avif'">
                    <div class="track-details">
                        <div class="track-title">${escapeHtml(track.track_title)}</div>
                        <div class="track-artist">${escapeHtml(track.artist_names || "Artiste inconnu")}</div>
                    </div>
                    <span class="pl-track-duration">${dur}</span>
                    <button class="pl-remove-btn" data-playlist-id="${playlist.playlist_id}" data-track-id="${track.track_id}" title="Retirer">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>
                    </button>
                    <div class="pl-inline-progress"><div class="pl-inline-progress-bar"></div></div>
                </div>
            `;
        });
    } else {
        tracksHtml = `
            <div class="pl-empty-state">
                <div class="pl-empty-icon">🎵</div>
                <p>Cette playlist est vide</p>
            </div>
        `;
    }

    const modal = $(`
        <div id="playlist-modal" class="modal show">
            <div class="modal-content">
                <div class="modal-header">
                    <div class="modal-header-covers">${coverGridHtml}</div>
                    <div class="modal-header-info">
                        <p class="pl-type">Playlist</p>
                        <h2>${escapeHtml(playlist.playlist_name)}</h2>
                        <p class="modal-description">${escapeHtml(playlist.playlist_description || "")}</p>
                        <p class="modal-tracks-count">${tracksCount} morceaux</p>
                    </div>
                    <span class="close-modal">&times;</span>
                </div>
                ${tracksCount > 0 ? `
                <div class="pl-actions-bar">
                    <button class="pl-play-all-btn" title="Tout écouter">
                        <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                    </button>
                    <button class="pl-shuffle-btn" title="Lecture aléatoire">
                        <svg viewBox="0 0 24 24"><path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/></svg>
                    </button>
                    <span class="pl-track-count-label">${tracksCount} titres</span>
                </div>` : ''}
                <div class="modal-tracks-list">
                    ${tracksHtml}
                </div>
            </div>
        </div>
    `).appendTo("body");

    document.body.style.overflow = 'hidden';

    let plCurrentTrackId = null;
    let plProgressInterval = null;
    let plPlayOrder = tracks.map((_, i) => i);
    let plPlayPos = -1;
    let plFetchedTracks = {};
    let plPreFetchStarted = false;

    function preFetchAllTracks() {
        if (plPreFetchStarted) return;
        plPreFetchStarted = true;
        tracks.forEach(t => {
            if (plFetchedTracks[t.track_id]) return;
            fetch(`${API_BASE_URL}/tracks/${t.track_id}`)
                .then(r => r.json())
                .then(track => {
                    plFetchedTracks[t.track_id] = {
                        url: track.track_file,
                        title: track.track_title,
                        artist: track.artist_info?.artist_name || 'Artiste inconnu'
                    };
                })
                .catch(() => {});
        });
    }

    function closeModal() {
        if (plProgressInterval) clearInterval(plProgressInterval);
        if (typeof audioPlayer !== 'undefined' && plCurrentTrackId && Object.keys(plFetchedTracks).length > 0) {
            const queueItems = plPlayOrder.map(idx => {
                const t = tracks[idx];
                const fetched = plFetchedTracks[t.track_id];
                if (!fetched) return null;
                return { url: fetched.url, title: fetched.title, artist: fetched.artist, trackId: t.track_id };
            }).filter(Boolean);
            if (queueItems.length > 0) {
                audioPlayer.setQueue(queueItems, Math.max(0, plPlayPos));
            }
            audioPlayer.onTrackEnd = null;
            audioPlayer.onNext = null;
            audioPlayer.onPrev = null;
        }
        modal.remove();
        document.body.style.overflow = '';
        $(document).off("keydown.playlistModal");
    }

    modal.find(".close-modal").on("click", closeModal);
    modal.on("click", function (event) {
        if ($(event.target).is(modal)) closeModal();
    });
    $(document).on("keydown.playlistModal", function (e) {
        if (e.key === "Escape") closeModal();
    });

    function playTrackInModal(trackId, rowEl) {
        if (!trackId || typeof audioPlayer === 'undefined') return;

        if (plCurrentTrackId == trackId && audioPlayer.audio && !audioPlayer.audio.paused) {
            audioPlayer.audio.pause();
            clearInterval(plProgressInterval);
            $(rowEl).removeClass('pl-playing');
            $(rowEl).find('.pl-play-icon').html('<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>');
            plCurrentTrackId = null;
            return;
        }

        modal.find('.modal-track-item').removeClass('pl-playing');
        modal.find('.pl-play-icon').html('<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>');
        modal.find('.pl-inline-progress-bar').css('width', '0%');

        preFetchAllTracks();

        const trackIdx = $(rowEl).data('index');
        const posInOrder = plPlayOrder.indexOf(trackIdx);
        if (posInOrder !== -1) plPlayPos = posInOrder;

        fetch(`${API_BASE_URL}/tracks/${trackId}`)
            .then(r => r.json())
            .then(track => {
                const trackUrl = track.track_file;
                const trackTitle = track.track_title;
                const trackArtist = track.artist_info?.artist_name || 'Artiste inconnu';

                plFetchedTracks[trackId] = { url: trackUrl, title: trackTitle, artist: trackArtist };

                audioPlayer.setSource('playlist', playlist.playlist_id, playlist.playlist_name);
                audioPlayer.playTrack({ url: trackUrl, title: trackTitle, artist: trackArtist, trackId });

                plCurrentTrackId = trackId;
                $(rowEl).addClass('pl-playing');
                $(rowEl).find('.pl-play-icon').html('<div class="pl-eq-bars"><span></span><span></span><span></span><span></span></div>');

                if (plProgressInterval) clearInterval(plProgressInterval);
                plProgressInterval = setInterval(() => {
                    if (audioPlayer.audio && audioPlayer.audio.duration) {
                        const pct = (audioPlayer.audio.currentTime / audioPlayer.audio.duration) * 100;
                        $(rowEl).find('.pl-inline-progress-bar').css('width', pct + '%');
                    }
                }, 300);

                function goToOffset(offset) {
                    const newPos = plPlayPos + offset;
                    if (newPos >= 0 && newPos < plPlayOrder.length) {
                        const nextTrackIdx = plPlayOrder[newPos];
                        const nextRow = modal.find(`.modal-track-item[data-index="${nextTrackIdx}"]`);
                        if (nextRow.length) {
                            playTrackInModal(tracks[nextTrackIdx].track_id, nextRow[0]);
                        }
                    } else if (offset > 0) {
                        audioPlayer.onTrackEnd = null;
                        audioPlayer.onNext = null;
                        audioPlayer.onPrev = null;
                        audioPlayer.stop();
                    }
                }

                audioPlayer.onTrackEnd = function () { goToOffset(1); };
                audioPlayer.onNext = function () { goToOffset(1); };
                audioPlayer.onPrev = function () {
                    if (audioPlayer.audio && audioPlayer.audio.currentTime > 3) {
                        audioPlayer.audio.currentTime = 0;
                    } else {
                        goToOffset(-1);
                    }
                };
            })
            .catch(err => console.error('Play error:', err));
    }

    modal.find('.modal-track-item').on('click', function (e) {
        if ($(e.target).closest('.pl-remove-btn').length) return;
        plPlayOrder = tracks.map((_, i) => i);
        const trackId = $(this).data('track-id');
        playTrackInModal(trackId, this);
    });

    modal.find('.pl-remove-btn').on('click', function (e) {
        e.stopPropagation();
        const plId = $(this).data('playlist-id');
        const tId = $(this).data('track-id');
        if (confirm("Retirer ce morceau de la playlist ?")) {
            fetch(`${API_BASE_URL}/playlists/${plId}/tracks/${tId}`, { method: "DELETE" })
                .then(res => {
                    if (res.ok) {
                        showNotification("Morceau retiré de la playlist", "success");
                        viewPlaylist(plId);
                        loadUserPlaylists(currentUserId);
                    } else {
                        showNotification("Erreur lors de la suppression", "error");
                    }
                })
                .catch(() => showNotification("Erreur lors de la suppression", "error"));
        }
    });

    modal.find('.pl-play-all-btn').on('click', function () {
        if (tracks.length > 0) {
            plPlayOrder = tracks.map((_, i) => i);
            plPlayPos = 0;
            const firstRow = modal.find('.modal-track-item').first();
            playTrackInModal(tracks[0].track_id, firstRow[0]);
        }
    });

    modal.find('.pl-shuffle-btn').on('click', function () {
        if (tracks.length > 0) {
            const shuffled = tracks.map((_, i) => i);
            for (let i = shuffled.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
            }
            plPlayOrder = shuffled;
            plPlayPos = 0;
            const firstIdx = shuffled[0];
            const firstRow = modal.find(`.modal-track-item[data-index="${firstIdx}"]`);
            playTrackInModal(tracks[firstIdx].track_id, firstRow[0]);
        }
    });
}

window.removeTrackFromPlaylist = async function (playlistId, trackId) {
    if (!confirm("Voulez-vous supprimer cette musique de la playlist ?")) return;

    try {
        const response = await fetch(`${API_BASE_URL}/playlists/${playlistId}/tracks/${trackId}`, { method: "DELETE" });

        if (response.ok) {
            showNotification("Musique supprimée de la playlist", "success");
            viewPlaylist(playlistId);
            loadUserPlaylists(currentUserId);
        } else {
            showNotification("Erreur lors de la suppression", "error");
        }
    } catch (error) {
        console.error("Erreur:", error);
        showNotification("Erreur lors de la suppression", "error");
    }
};

// ===== NOTIFICATIONS =====
function showNotification(message, type = "info") {
    $(".notification").remove();

    const notification = $(`
        <div class="notification notification-${type}">
            ${message}
            <span class="notification-close">&times;</span>
        </div>
    `).appendTo("body");

    notification.find(".notification-close").on("click", function () {
        notification.remove();
    });

    setTimeout(() => {
        notification.fadeOut(() => notification.remove());
    }, 5000);
}

// ===== UTILITAIRES =====
function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function formatDate(dateString) {
    if (!dateString) return "Date inconnue";
    const date = new Date(dateString);
    return date.toLocaleDateString("fr-FR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric"
    });
}

window.openPlayerSource = function (type, id, name) {
    if (type === 'playlist' && id) {
        viewPlaylist(id);
    } else if (type === 'album' || type === 'artist') {
        window.location.href = 'accueil.html';
    }
};