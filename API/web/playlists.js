// Configuration
const API_BASE_URL = "http://127.0.0.1:8000";
const AUTH_API_URL = "http://localhost:3000";
let currentUserId = null;
let selectedTracks = []; // Tracks sélectionnées pour la création

// Initialisation
$(document).ready(function() {
    // Vérifier l'utilisateur connecté
    checkAuthenticatedUser();
    
    // Configurer l'autocomplete pour la recherche de tracks
    setupTrackSearch();
    
    // Gestionnaire pour le bouton de création
    $("#create-playlist-button").on("click", createPlaylist);
});

// Vérifier l'utilisateur connecté
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
        currentUserId = 1; // ID par défaut
        loadUserPlaylists(currentUserId);
    }
}

// Charger les playlists de l'utilisateur
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

// Afficher les playlists
function displayPlaylists(playlists) {
    const container = $(".playlists-container");
    container.empty();
    
    if (playlists.length === 0) {
        container.html(`
            <div class="empty-state">
                <p>Vous n'avez pas encore de playlist</p>
                <p>Créez votre première playlist ci-dessus !</p>
            </div>
        `);
        return;
    }
    
    playlists.forEach(playlist => {
        const playlistCard = createPlaylistCard(playlist);
        container.append(playlistCard);
    });
}

// Créer une carte de playlist
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
                    <span>${playlist.tracks_count || 0} titres</span>
                    <span>Créée le ${formatDate(playlist.created_at)}</span>
                </div>
                <div class="playlist-actions">
                    <button class="btn-view" onclick="viewPlaylist(${playlist.playlist_id})">
                        <span class="icon">👁️</span> Voir
                    </button>
                    <button class="btn-delete" onclick="deletePlaylist(${playlist.playlist_id})">
                        <span class="icon">🗑️</span> Supprimer
                    </button>
                </div>
            </div>
        </div>
    `);
    
    return card;
}

// Générer la grille d'images pour la playlist
function generatePlaylistCovers(tracks) {
    if (tracks.length === 0) {
        return `<div class="no-cover">🎵</div>`;
    }
    
    let html = '<div class="cover-grid">';
    tracks.slice(0, 4).forEach(track => {
        let imageUrl = getTrackImageUrl(track);
        html += `<div class="cover-item">
            <img src="${imageUrl}" alt="${escapeHtml(track.track_title)}" onerror="this.src='images/no_image_music.png'">
        </div>`;
    });
    
    // Compléter avec des placeholders si moins de 4 images
    for (let i = tracks.length; i < 4; i++) {
        html += `<div class="cover-item">
            <img src="images/no_image_music.png" alt="Aucune image">
        </div>`;
    }
    
    html += '</div>';
    return html;
}

// Obtenir l'URL de l'image d'une track
function getTrackImageUrl(track) {
    if (track.track_image_file) {
        const match = track.track_image_file.match(/([^/]+\.(jpg|png|jpeg))$/i);
        const filename = match ? match[1] : track.track_image_file;
        if (filename) {
            return `https://freemusicarchive.org/image/?file=images%2Falbums%2F${filename}&width=290&height=290&type=album`;
        }
    }
    return 'images/no_image_music.png';
}

// Configurer la recherche automatique de tracks
function setupTrackSearch() {
    const searchInput = $("#track-search-input");
    
    searchInput.autocomplete({
        source: async function(request, response) {
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
        select: function(event, ui) {
            addTrackToSelection(ui.item.id, ui.item.label, ui.item.image);
            $(this).val("");
            return false;
        }
    }).autocomplete("instance")._renderItem = function(ul, item) {
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

// Ajouter une track à la sélection
function addTrackToSelection(trackId, trackTitle, imageUrl) {
    // Vérifier si déjà sélectionné
    if (selectedTracks.some(t => t.id === trackId)) {
        showNotification("Cette musique est déjà dans la sélection", "info");
        return;
    }
    
    const track = { id: trackId, title: trackTitle, image: imageUrl };
    selectedTracks.push(track);
    
    displaySelectedTracks();
}

// Afficher les tracks sélectionnées
function displaySelectedTracks() {
    const container = $("#selected-tracks-container");
    container.empty();
    
    if (selectedTracks.length === 0) {
        container.html('<p class="no-selection">Aucune musique sélectionnée</p>');
        return;
    }
    
    selectedTracks.forEach((track, index) => {
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

// Supprimer une track de la sélection
window.removeTrackFromSelection = function(trackId) {
    selectedTracks = selectedTracks.filter(t => t.id !== trackId);
    displaySelectedTracks();
};

// Créer une playlist
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
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                name: name,
                description: description,
                user_id: currentUserId,
                track_ids: trackIds
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification("Playlist créée avec succès !", "success");
            
            // Réinitialiser le formulaire
            $("#playlist-name-input").val("");
            $("#playlist-description-input").val("");
            selectedTracks = [];
            displaySelectedTracks();
            
            // Recharger les playlists
            loadUserPlaylists(currentUserId);
        } else {
            showNotification("Erreur lors de la création", "error");
        }
    } catch (error) {
        console.error("Erreur:", error);
        showNotification("Erreur lors de la création de la playlist", "error");
    }
}

// Voir une playlist (redirection ou modal)
window.viewPlaylist = function(playlistId) {
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

// Supprimer une playlist
window.deletePlaylist = async function(playlistId) {
    if (!confirm("Êtes-vous sûr de vouloir supprimer cette playlist ?")) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/playlists/${playlistId}`, {
            method: "DELETE"
        });
        
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

// Afficher une modal avec les détails de la playlist
function showPlaylistModal(playlist) {
    // Créer la modal si elle n'existe pas
    let modal = $("#playlist-modal");
    if (modal.length === 0) {
        modal = $(`
            <div id="playlist-modal" class="modal">
                <div class="modal-content">
                    <span class="close-modal">&times;</span>
                    <h2 id="modal-playlist-title"></h2>
                    <p id="modal-playlist-description" class="modal-description"></p>
                    <div class="modal-tracks-list"></div>
                </div>
            </div>
        `).appendTo("body");
        
        modal.find(".close-modal").on("click", function() {
            modal.hide();
        });
        
        $(window).on("click", function(event) {
            if ($(event.target).is(modal)) {
                modal.hide();
            }
        });
    }
    
    // Remplir la modal
    modal.find("#modal-playlist-title").text(playlist.playlist_name);
    modal.find("#modal-playlist-description").text(playlist.playlist_description || "Aucune description");
    
    const tracksList = modal.find(".modal-tracks-list");
    tracksList.empty();
    
    if (playlist.tracks && playlist.tracks.length > 0) {
        playlist.tracks.forEach(track => {
            const trackItem = $(`
                <div class="modal-track-item track-card" data-track-id="${track.track_id}">
                    <img src="${getTrackImageUrl(track)}" alt="" class="track-image">
                    <div class="track-details">
                        <div class="track-title">${escapeHtml(track.track_title)}</div>
                        <div class="track-artist">${escapeHtml(track.artist_names || "Artiste inconnu")}</div>
                    </div>
                    <button class="btn-remove-track" onclick="removeTrackFromPlaylist(${playlist.playlist_id}, ${track.track_id})">
                        Supprimer
                    </button>
                </div>
            `);
            tracksList.append(trackItem);
        });
    } else {
        tracksList.html('<p class="no-tracks">Aucune musique dans cette playlist</p>');
    }
    
    modal.show();
}

// Supprimer une track d'une playlist
window.removeTrackFromPlaylist = async function(playlistId, trackId) {
    if (!confirm("Voulez-vous supprimer cette musique de la playlist ?")) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/playlists/${playlistId}/tracks/${trackId}`, {
            method: "DELETE"
        });
        
        if (response.ok) {
            showNotification("Musique supprimée de la playlist", "success");
            // Recharger la playlist pour mettre à jour la modal
            viewPlaylist(playlistId);
            // Recharger les playlists pour mettre à jour les aperçus
            loadUserPlaylists(currentUserId);
        } else {
            showNotification("Erreur lors de la suppression", "error");
        }
    } catch (error) {
        console.error("Erreur:", error);
        showNotification("Erreur lors de la suppression", "error");
    }
};

// Afficher une notification
function showNotification(message, type = "info") {
    // Supprimer les anciennes notifications
    $(".notification").remove();
    
    const notification = $(`
        <div class="notification notification-${type}">
            ${message}
            <span class="notification-close">&times;</span>
        </div>
    `).appendTo("body");
    
    notification.find(".notification-close").on("click", function() {
        notification.remove();
    });
    
    setTimeout(() => {
        notification.fadeOut(() => notification.remove());
    }, 5000);
}

// Échapper les caractères HTML
function escapeHtml(unsafe) {
    if (!unsafe) return "";
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

// Formater la date
function formatDate(dateString) {
    if (!dateString) return "Date inconnue";
    const date = new Date(dateString);
    return date.toLocaleDateString("fr-FR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric"
    });
}