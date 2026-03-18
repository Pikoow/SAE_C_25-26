// Fonction pour ajouter un élément (badge) dans une liste
function ajouterElementSelectionne(nom, containerId, idElement) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const uniqueHtmlId = `badge-${containerId}-${idElement}`;
    if (document.getElementById(uniqueHtmlId)) return;

    const badge = document.createElement("div");
    badge.className = "badge-item";
    badge.id = uniqueHtmlId; 
    badge.setAttribute('data-id', idElement); 
    badge.title = "Cliquez pour supprimer";
    badge.innerHTML = `<span>${nom}</span>`;

    badge.addEventListener("click", function() {
        this.remove();
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
    if (!userId) return alert("Veuillez vous connecter.");

    const choixUtilisateur = confirm("Voulez-vous enregistrer vos préférences ?");

    if (choixUtilisateur) {
        const getIds = (containerId) => {
            const badges = document.querySelectorAll(`#${containerId} .badge-item`);
            return Array.from(badges).map(badge => String(badge.getAttribute('data-id')));
        };

        const payload = {
            user_id: parseInt(userId),
            genres: getIds("selected-genres-list"),
            artists: getIds("selected-artists-list"),
            tracks: getIds("selected-tracks-list")
        };

        console.log("Données envoyées au main.py :", payload);

        try {
            const response = await fetch("http://127.0.0.1:8000/save-favorites", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            if (result.success) {
                console.log("Vos préférences ont été enregistrées !");
            }
            else{
                console.log("Erreur : " + (result.error || "Problème lors de la sauvegarde"));
            }
        } catch (err) {
            console.error("Erreur de connexion à l'API Python :", err);
        }
        console.log("Préférences enregistrées.");
    } else {
        console.log("Action annulée.");
    }
}

// Vide toutes les listes
function Reset() {
    const choixUtilisateur = confirm("Voulez-vous vraiment supprimer vos préférences ?");

    if (choixUtilisateur) {
        $('.selected-list-container').empty();
        $('#selected-genres-list, #selected-artists-list, #selected-tracks-list').empty();
        console.log("Préférences supprimées.");
    } else {
        console.log("Action annulée.");
    }
}

//Fonction pour remplir avec les anciennes données de user
async function chargerPreferencesUtilisateur() {
    const userId = localStorage.getItem("userId") || 1;
    const response = await fetch(`http://127.0.0.1:8000/voir_favorite/${userId}`);
    const result = await response.json();
    if (result.count !== 0) {
        const data = result.results;
        const mappings = [
            { data: data[0].user_favorite_genre, container: 'selected-genres-list' },
            { data: data[0].user_favorite_artist, container: 'selected-artists-list' },
            { data: data[0].user_favorite_tracks, container: 'selected-tracks-list' }
        ];
        mappings.forEach(map => {
            if (map.data) {
                const items = map.data.split(',');
                
                items.forEach((item, index) => {
                    const cleanName = item.trim();
                    if (cleanName !== "") {
                        ajouterElementSelectionne(cleanName, map.container, `load-${index}`);
                    }
                });
            }
        });
    }
}


// Initialisation
$(document).ready(function() {
    initPage();
});

/* Reactions: Like / Dislike / Favorite helpers */
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
        controls.innerHTML = `
            <button class="btn-like">👍</button>
            <button class="btn-dislike">👎</button>
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

//Pour lancer les fonctions en parrallèles
async function initPage() {
    console.time("ChargementParallèle");

    await Promise.all([
        chargerPreferencesUtilisateur(),
        chargerGenres(),//1.41
        chargerArtists(),//2.61
        chargerMusiques()//600
        //1400
    ]);

    // console.log("Toutes les ressources sont chargées !");
}

/****************************************
 *********** C A R R O U S E L **********
 ****************************************/



// const carousel_buttons = document.querySelectorAll(".carousel-button");
// const carousel_slides = document.querySelectorAll(".carousel-slide");
// // console.log(carousel_buttons,carousel_slides)
// let currentIndex = 3
// carousel_buttons.forEach((carrBut) => {
//     carrBut.addEventListener('click', (e) => {
        
//         const direction = e.target.id === 'next' ? 1 : -1;
//         const total = carousel_slides.length;

//         currentIndex = (currentIndex + direction + total) % total;

//         const new_left  = (currentIndex - 1 + total) % total;
//         const new_right = (currentIndex + 1) % total;

//         console.log(new_left, currentIndex, new_right);

//         carousel_slides.forEach(slide =>
//             slide.classList.remove("active")
//         );

//         carousel_slides[currentIndex].classList.add("active");
//         carousel_slides[new_left].classList.add("active");
//         carousel_slides[new_right].classList.add("active");
//     })
// })



const carousel_buttons_artist = document.querySelectorAll(".carousel-button-artist");
const carousel_slides_artist = document.querySelectorAll(".artist-card-carousel");
// console.log(carousel_buttons,carousel_slides)
let artist_index = 0
carousel_buttons_artist.forEach((carrBut) => {
    carrBut.addEventListener('click', (e) => {
        
        const direction = e.target.id === 'next-artist' ? 1 : -1;
        const total = carousel_slides.length;

        artist_index = (artist_index + direction + total) % total;

        const new_left  = (artist_index - 1 + total) % total;
        const new_right = (artist_index + 1) % total;

        console.log(new_left, artist_index, new_right);

        carousel_slides.forEach(slide =>
            slide.classList.remove("active")
        );

        carousel_slides[artist_index].classList.add("active");
        carousel_slides[new_left].classList.add("active");
        carousel_slides[new_right].classList.add("active");
    })
})

const carousel_buttons_track = document.querySelectorAll(".carousel-button-track");
const carousel_slides_track = document.querySelectorAll(".track-card");
// console.log(carousel_buttons,carousel_slides)
let track_index = 0
carousel_buttons_track.forEach((carrBut) => {
    carrBut.addEventListener('click', (e) => {
        
        const direction = e.target.id === 'next-track' ? 1 : -1;
        const total = carousel_slides.length;

        track_index = (track_index + direction + total) % total;

        const new_left  = (track_index - 1 + total) % total;
        const new_right = (track_index + 1) % total;

        console.log(new_left, currentIndex, new_right); 

        carousel_slides.forEach(slide =>
            slide.classList.remove("active")
        );

        carousel_slides[track_index].classList.add("active");
        carousel_slides[new_left].classList.add("active");
        carousel_slides[new_right].classList.add("active");
    })
})