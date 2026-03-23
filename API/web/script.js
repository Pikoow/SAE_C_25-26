// Fonction pour ajouter un élément (badge) dans une liste
function ajouterElementSelectionne(nom, containerId, idElement) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Utilisation de l'ID réel pour éviter les doublons et les erreurs de sauvegarde
    const uniqueHtmlId = `badge-${containerId}-${idElement}`;
    if (document.getElementById(uniqueHtmlId)) return;

    const badge = document.createElement("div");
    badge.className = "badge-item";
    badge.id = uniqueHtmlId;
    badge.setAttribute('data-id', idElement); // Crucial pour la sauvegarde
    
    badge.innerHTML = `
        <span class="badge-label">${nom}</span>
        <button class="badge-remove" title="Supprimer">×</button>
    `;

    // Suppression : UNIQUEMENT lors du clic sur la croix
    const removeBtn = badge.querySelector('.badge-remove');
    removeBtn.addEventListener('click', function(e) {
        e.stopPropagation(); // Évite tout conflit
        badge.remove();
    });

    container.appendChild(badge);
}

// Autocomplete pour les Genres
async function chargerGenres() {
    const inputElement = document.getElementById("genre");
    if (!inputElement) return;

    try {
        const response = await fetch("http://127.0.0.1:8000/genres");
        const genres = await response.json();

        $(inputElement).autocomplete({
            source: function(request, response) {
                const term = request.term.toLowerCase();
                const matches = (genres.results || genres)
                    .filter(g => (g.genre_title || "").toLowerCase().includes(term))
                    .slice(0, 15)
                    .map(g => ({ label: g.genre_title, value: g.genre_title, id: g.genre_id }));
                response(matches);
            },
            minLength: 1,
            select: function(event, ui) {
                ajouterElementSelectionne(ui.item.value, "selected-genres-list", ui.item.id);
                $(this).val("");
                return false;
            }
        });
    } catch (error) {
        console.error("Erreur Genres :", error);
    }
}

// Autocomplete pour les Artistes
async function chargerArtists() {
    const inputElement = document.getElementById("artistes");
    if (!inputElement) return;

    try {
        const response = await fetch("http://127.0.0.1:8000/artists");
        const artists = await response.json();

        $(inputElement).autocomplete({
            source: function(request, response) {
                const term = request.term.toLowerCase();
                const matches = (artists.results || artists)
                    .filter(a => (a.artist_name || "").toLowerCase().includes(term))
                    .slice(0, 15)
                    .map(a => ({ label: a.artist_name, value: a.artist_name, id: a.artist_id }));
                response(matches);
            },
            minLength: 1,
            select: function(event, ui) {
                ajouterElementSelectionne(ui.item.value, "selected-artists-list", ui.item.id);
                $(this).val("");
                return false;
            }
        });
    } catch (error) {
        console.error("Erreur Artistes :", error);
    }
}

// Autocomplete pour les Musiques
async function chargerMusiques() {
    const inputElement = document.getElementById("musique");
    if (!inputElement) return;

    try {
        const response = await fetch("http://127.0.0.1:8000/tracks");
        const data = await response.json();
        const tracks = data.results || [];

        $(inputElement).autocomplete({
            source: function(request, response) {
                const term = request.term.toLowerCase();
                const matches = tracks
                    .filter(t => t.track_title.toLowerCase().includes(term))
                    .slice(0, 15)
                    .map(t => ({
                        label: `${t.track_title} (${t.album_title || 'Single'})`,
                        value: t.track_title,
                        id: t.track_id
                    }));
                response(matches);
            },
            minLength: 1,
            select: function(event, ui) {
                ajouterElementSelectionne(ui.item.value, "selected-tracks-list", ui.item.id);
                $(this).val("");
                return false;
            }
        });
    } catch (error) {
        console.error("Erreur Musiques :", error);
    }
}

//Fonction pour sauvegarder les preferences de user
async function Sauvegarde() {
    const userId = localStorage.getItem("userId");
    if (!userId) {
        return Swal.fire({
            icon: 'warning',
            title: 'Non connecté',
            text: 'Veuillez vous connecter pour sauvegarder vos préférences.',
            confirmButtonColor: '#ed7a26'
        });
    }

    const confirmation = await Swal.fire({
        title: 'Sauvegarder ?',
        text: 'Voulez-vous enregistrer vos préférences ?',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#ed7a26',
        cancelButtonColor: '#aaa',
        confirmButtonText: 'Sauvegarder',
        cancelButtonText: 'Annuler',
        reverseButtons: true
    });

    if (confirmation.isConfirmed) {
        const getIds = (containerId) => {
            const badges = document.querySelectorAll(`#${containerId} .badge-item`);
            return Array.from(badges)
                .map(badge => badge.getAttribute('data-id'))
                .filter(id => id && !id.startsWith('load-')); 
        };

        const payload = {
            user_id: parseInt(userId),
            genres: getIds("selected-genres-list"),
            artists: getIds("selected-artists-list"),
            tracks: getIds("selected-tracks-list")
        };

        try {
            const response = await fetch("http://127.0.0.1:8000/save-favorites", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            if (result.success) {
                Swal.fire({
                    icon: 'success',
                    title: 'Sauvegardé !',
                    text: 'Vos préférences ont été enregistrées avec succès.',
                    confirmButtonColor: '#ed7a26',
                    timer: 2500,
                    showConfirmButton: false
                });
            } else {
                Swal.fire({
                    icon: 'error',
                    title: 'Erreur',
                    text: 'Une erreur est survenue lors de la sauvegarde.',
                    confirmButtonColor: '#ed7a26'
                });
                console.error("Erreur API:", result.error);
            }
        } catch (err) {
            Swal.fire({
                icon: 'error',
                title: 'Erreur de connexion',
                text: 'Impossible de contacter le serveur.',
                confirmButtonColor: '#ed7a26'
            });
            console.error("Erreur de connexion :", err);
        }
    }
}

// Vide toutes les listes
async function Reset() {
    const confirmation = await Swal.fire({
        title: 'Réinitialiser ?',
        text: 'Voulez-vous vraiment supprimer toutes vos préférences ?',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e74c3c',
        cancelButtonColor: '#aaa',
        confirmButtonText: 'Supprimer tout',
        cancelButtonText: 'Annuler',
        reverseButtons: true
    });

    if (confirmation.isConfirmed) {
        $('.selected-list-container').empty();
        $('#selected-genres-list, #selected-artists-list, #selected-tracks-list').empty();
        Swal.fire({
            icon: 'success',
            title: 'Réinitialisé',
            text: 'Vos préférences ont été supprimées.',
            confirmButtonColor: '#ed7a26',
            timer: 2000,
            showConfirmButton: false
        });
    }
}

//Fonction pour remplir avec les anciennes données de user
async function chargerPreferencesUtilisateur() {
    const userId = localStorage.getItem("userId") || 1;
    try {
        const response = await fetch(`http://127.0.0.1:8000/voir_favorite/${userId}`);
        const result = await response.json();
        
        if (result.count !== 0 && result.results[0]) {
            const data = result.results[0];
            
            // On traite chaque catégorie en liant les noms avec leurs vrais IDs
            const categories = [
                { items: data.user_favorite_genre, ids: data.ids_genres, container: 'selected-genres-list' },
                { items: data.user_favorite_artist, ids: data.ids_artists, container: 'selected-artists-list' },
                { items: data.user_favorite_tracks, ids: data.ids_tracks, container: 'selected-tracks-list' }
            ];

            categories.forEach(cat => {
                if (cat.items && cat.ids) {
                    const names = cat.items.split(',');
                    const ids = cat.ids.split(',');

                    names.forEach((name, index) => {
                        const cleanName = name.trim();
                        // On utilise l'ID réel ou on crée un fallback si par hasard il y a un décalage
                        const cleanId = ids[index] ? ids[index].trim() : `load-${index}-${Date.now()}`;
                        
                        if (cleanName) {
                            ajouterElementSelectionne(cleanName, cat.container, cleanId);
                        }
                    });
                }
            });
        }
    } catch (err) {
        console.error("Erreur lors du chargement des préférences :", err);
    }
}


// Initialisation
$(document).ready(function() {
    initPage();
});

//Pour lancer les fonctions en parrallèles
async function initPage() {
    console.time("ChargementParallèle");

    await Promise.all([
        chargerPreferencesUtilisateur(),
        chargerGenres(),
        chargerArtists(),
        chargerMusiques()
    ]);

    console.timeEnd("ChargementParallèle");
}
async function toggleReaction(targetType, targetId, action, value) {
    const userId = localStorage.getItem("userId");
    if (!userId) return alert("Veuillez vous connecter pour interagir.");

    try {
        const res = await fetch(`http://127.0.0.1:8000/reactions/${targetType}/${targetId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: parseInt(userId), action: action, value: value })
        });
        const data = await res.json();
        if (!data.success) console.warn('Reaction failed', data);
        return data.reaction;
    } catch (err) {
        console.error('Erreur reaction', err);
        throw err;
    }
}

async function getReactionState(targetType, targetId) {
    const userId = localStorage.getItem("userId");
    if (!userId) return { liked: false, disliked: false, favorite: false };
    try {
        const res = await fetch(`http://127.0.0.1:8000/reactions/${targetType}/${targetId}/${userId}`);
        if (!res.ok) return { liked: false, disliked: false, favorite: false };
        return await res.json();
    } catch (err) {
        console.error('Erreur getReactionState', err);
        return { liked: false, disliked: false, favorite: false };
    }
}

// Helper to attach buttons inside a container element representing an entity
function attachReactionButtons(containerEl, targetType, targetId) {
    if (!containerEl) return;
    // Create buttons if they don't exist
    if (!containerEl.querySelector('.reaction-controls')) {
        const controls = document.createElement('div');
        controls.className = 'reaction-controls';
        // Remplacement des émojis par les icônes SVG
        controls.innerHTML = `
            <button class="btn-like" title="Like"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg></button>
            <button class="btn-dislike" title="Dislike"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-2"></path></svg></button>
        `;
        containerEl.appendChild(controls);

        const btnLike = controls.querySelector('.btn-like');
        const btnDislike = controls.querySelector('.btn-dislike');
        const userId = localStorage.getItem('userId');

        // disable buttons for anonymous users
        if (!userId) {
            btnLike.disabled = true;
            btnDislike.disabled = true;
            btnLike.title = 'Connexion requise';
            btnDislike.title = 'Connexion requise';
            btnLike.style.opacity = '0.5';
            btnDislike.style.opacity = '0.5';
            btnLike.style.cursor = 'not-allowed';
            btnDislike.style.cursor = 'not-allowed';
        }

        // Wire click handlers
        btnLike.addEventListener('click', async () => {
            try {
                const state = await getReactionState(targetType, targetId);
                const newVal = !state.liked;
                const serverState = await toggleReaction(targetType, targetId, 'like', newVal);
                updateReactionUI(controls, serverState || { liked: newVal, disliked: newVal ? false : state.disliked, favorite: state.favorite });
            } catch (e) { console.error('reaction error', e); }
        });

        btnDislike.addEventListener('click', async () => {
            try {
                const state = await getReactionState(targetType, targetId);
                const newVal = !state.disliked;
                const serverState = await toggleReaction(targetType, targetId, 'dislike', newVal);
                updateReactionUI(controls, serverState || { liked: newVal ? false : state.liked, disliked: newVal, favorite: state.favorite });
            } catch (e) { console.error('reaction error', e); }
        });

        // initialize state
        getReactionState(targetType, targetId).then(state => updateReactionUI(controls, state));
    }
}

function updateReactionUI(controlsEl, state) {
    if (!controlsEl) return;
    const btnLike = controlsEl.querySelector('.btn-like');
    const btnDislike = controlsEl.querySelector('.btn-dislike');
    if (state.liked) btnLike.classList.add('active'); else btnLike.classList.remove('active');
    if (state.disliked) btnDislike.classList.add('active'); else btnDislike.classList.remove('active');
}

// Expose helpers to global window for other scripts (player)
window.getReactionState = getReactionState;
window.toggleReaction = toggleReaction;
window.attachReactionButtons = attachReactionButtons;



/****************************************
 *********** C A R R O U S E L **********
 ****************************************/

const carousel_buttons_artist = document.querySelectorAll(".carousel-button-artist");
const carousel_slides_artist = document.querySelectorAll(".artist-card-carousel");

let artist_index = 0
carousel_buttons_artist.forEach((carrBut) => {
    carrBut.addEventListener('click', (e) => {
        
        const direction = e.target.id === 'next-artist' ? 1 : -1;
        const total = carousel_slides_artist.length; // Correction de l'appel aux slides

        artist_index = (artist_index + direction + total) % total;

        const new_left  = (artist_index - 1 + total) % total;
        const new_right = (artist_index + 1) % total;

        console.log(new_left, artist_index, new_right);

        carousel_slides_artist.forEach(slide =>
            slide.classList.remove("active")
        );

        carousel_slides_artist[artist_index].classList.add("active");
        carousel_slides_artist[new_left].classList.add("active");
        carousel_slides_artist[new_right].classList.add("active");
    })
})

const carousel_buttons_track = document.querySelectorAll(".carousel-button-track");
const carousel_slides_track = document.querySelectorAll(".track-card");

let track_index = 0
carousel_buttons_track.forEach((carrBut) => {
    carrBut.addEventListener('click', (e) => {
        
        const direction = e.target.id === 'next-track' ? 1 : -1;
        const total = carousel_slides_track.length; // Correction de l'appel aux slides

        track_index = (track_index + direction + total) % total;

        const new_left  = (track_index - 1 + total) % total;
        const new_right = (track_index + 1) % total;

        console.log(new_left, track_index, new_right); 

        carousel_slides_track.forEach(slide =>
            slide.classList.remove("active")
        );

        carousel_slides_track[track_index].classList.add("active");
        carousel_slides_track[new_left].classList.add("active");
        carousel_slides_track[new_right].classList.add("active");
    })
})