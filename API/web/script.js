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

// Vide toutes les listes
function Reset() {
    $('.selected-list-container').empty();
    $('#selected-genres-list, #selected-artists-list, #selected-tracks-list').empty();
}

// Initialisation
$(document).ready(function() {
    chargerGenres();
    chargerArtists();
    chargerMusiques();
});


/****************************************
 *********** C A R R O U S E L **********
 ****************************************/



// const carrousel_buttons = document.querySelectorAll(".carrousel-button");
// const carrousel_slides = document.querySelectorAll(".carrousel-slide");
// // console.log(carrousel_buttons,carrousel_slides)
// let currentIndex = 3
// carrousel_buttons.forEach((carrBut) => {
//     carrBut.addEventListener('click', (e) => {
        
//         const direction = e.target.id === 'next' ? 1 : -1;
//         const total = carrousel_slides.length;

//         currentIndex = (currentIndex + direction + total) % total;

//         const new_left  = (currentIndex - 1 + total) % total;
//         const new_right = (currentIndex + 1) % total;

//         console.log(new_left, currentIndex, new_right);

//         carrousel_slides.forEach(slide =>
//             slide.classList.remove("active")
//         );

//         carrousel_slides[currentIndex].classList.add("active");
//         carrousel_slides[new_left].classList.add("active");
//         carrousel_slides[new_right].classList.add("active");
//     })
// })



const carrousel_buttons_artist = document.querySelectorAll(".carrousel-button-artist");
const carrousel_slides_artist = document.querySelectorAll(".artist-card-carrousel");
// console.log(carrousel_buttons,carrousel_slides)
let artist_index = 0
carrousel_buttons_artist.forEach((carrBut) => {
    carrBut.addEventListener('click', (e) => {
        
        const direction = e.target.id === 'next-artist' ? 1 : -1;
        const total = carrousel_slides.length;

        artist_index = (artist_index + direction + total) % total;

        const new_left  = (artist_index - 1 + total) % total;
        const new_right = (artist_index + 1) % total;

        console.log(new_left, artist_index, new_right);

        carrousel_slides.forEach(slide =>
            slide.classList.remove("active")
        );

        carrousel_slides[artist_index].classList.add("active");
        carrousel_slides[new_left].classList.add("active");
        carrousel_slides[new_right].classList.add("active");
    })
})

const carrousel_buttons_track = document.querySelectorAll(".carrousel-button-track");
const carrousel_slides_track = document.querySelectorAll(".track-card");
// console.log(carrousel_buttons,carrousel_slides)
let track_index = 0
carrousel_buttons_track.forEach((carrBut) => {
    carrBut.addEventListener('click', (e) => {
        
        const direction = e.target.id === 'next-track' ? 1 : -1;
        const total = carrousel_slides.length;

        track_index = (track_index + direction + total) % total;

        const new_left  = (track_index - 1 + total) % total;
        const new_right = (track_index + 1) % total;

        console.log(new_left, currentIndex, new_right); 

        carrousel_slides.forEach(slide =>
            slide.classList.remove("active")
        );

        carrousel_slides[track_index].classList.add("active");
        carrousel_slides[new_left].classList.add("active");
        carrousel_slides[new_right].classList.add("active");
    })
})