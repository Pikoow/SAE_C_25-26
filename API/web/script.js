// Fonction Gestion des elements des liste(Ajouter/Supression)
function ajouterElementSelectionne(nom, containerId, idElement) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // On crée un ID HTML unique pour éviter les doublons entre listes
    // Exemple : "badge-selected-artists-list-152"
    const uniqueHtmlId = `badge-${containerId}-${idElement}`;

    if (document.getElementById(uniqueHtmlId)) {
        console.warn("Cet élément est déjà sélectionné dans cette liste");
        return;
    }

    const badge = document.createElement("div");
    badge.className = "badge-item";
    badge.id = uniqueHtmlId; 
    // TRÈS IMPORTANT : On stocke l'ID SQL pur ici
    badge.setAttribute('data-id', idElement); 
    
    badge.title = "Cliquez pour supprimer";
    badge.innerHTML = `<span>${nom}</span>`;

    badge.addEventListener("click", function() {
        this.style.transform = "scale(0)";
        this.style.opacity = "0";
        
    });

    container.appendChild(badge);

    if(containerId === "selected-genres-list") chargerArtists();
    if (containerId === "selected-artists-list") chargerMusiques();
}

// Fonction pour l'Autocomplete des Genres
async function chargerGenres() {
    const inputElement = document.getElementById("genre");
    if (!inputElement) return;

    try {
        const response = await fetch("http://127.0.0.1:8000/genres");
        const data = await response.json();
        const genres = data.results || data;

        if (Array.isArray(genres)) {
            const ListeGenres = genres.map(g => ({
                label : g.genre_title || "Sans titre",
                value : g.genre_title || "Sans titre",
                id : g.genre_id
            }));

            $(inputElement).autocomplete({
                source: function(request, response) {
                    const term = request.term.toLowerCase();
                    const matches = ListeGenres.filter(item => item.label.toLowerCase().includes(term)).slice(0, 15);
                    response(matches);
                },
                minLength: 1,
                select: function(event, ui) {
                    ajouterElementSelectionne(ui.item.value, "selected-genres-list",ui.item.id);
                    $(this).val("");
                    return false;
                }
            });
            
            console.log("Autocomplete Genres prêt !");
        }
    } catch (error) {
        console.error("Erreur lors du chargement des genres :", error);
    }
}

// Fonction pour l'Autocomplete des Artistes
async function chargerArtists() {
    const inputElement = document.getElementById("artistes");
    const elements = document.querySelectorAll('.badge-item');

    const url = `http://127.0.0.1:8000/artists`;
    
    try {
        const response = await fetch(url);
        const data = await response.json();
        const artists = data.results || data;

        if (Array.isArray(artists)) {
            const listeArtistes = artists.map(a => ({
                label : a.artist_name || "Sans titre",
                value : a.artist_name || "Sans titre",
                id : a.artist_id
            }));

            $(inputElement).autocomplete({
                source: function(request, response) {
                    const term = request.term.toLowerCase();
                    const matches = listeArtistes.filter(item => item.label.toLowerCase().includes(term)).slice(0, 15);
                    response(matches);
                },
                minLength: 1,
                select: function(event, ui) {
                    ajouterElementSelectionne(ui.item.value, "selected-artists-list", ui.item.id);
                    $(this).val("");
                    return false;
                }
            });
            console.log("Autocomplete Artistes prêt !");
        }
    } catch (error) {
        console.error("Erreur Artistes :", error);
    }
}

// Fonction pour l'Autocomplete des Musiques
async function chargerMusiques() {
    const inputElement = document.getElementById("musique");

    const url = `http://127.0.0.1:8000/tracks`;

    try {
        const response = await fetch(url);
        const data = await response.json();
        const tracks = data.results || [];

        const listeMusiques = tracks.map(t => ({
            label: `${t.track_title} (${t.album_title || 'Single'})`,
            value: t.track_title,
            id: t.track_id
        }));

        $(inputElement).autocomplete({
            source: function(request, response) {
                const term = request.term.toLowerCase();
                const matches = listeMusiques.filter(item => item.label.toLowerCase().includes(term)).slice(0, 15);
                response(matches);
            },
            minLength: 1,
            select: function(event, ui) {
                ajouterElementSelectionne(ui.item.value, "selected-tracks-list", ui.item.id);
                $(this).val("");
                return false;
            }
        });
        console.log("Autocomplete Musique prêt !");
    } catch (error) {
        console.error("Erreur Fetch Musiques :", error);
    }
}

/* Bouton pour faire des recommendations
async function Sauvegarde() {
    const container = document.getElementById("selected-tracks-list");
    const displayElement = document.getElementById("tracks-container"); 
    
    if (!container || !displayElement) return;

    const elements = container.querySelectorAll('.badge-item');

    const queryParams = new URLSearchParams();
    elements.forEach(el => {
        const id = el.getAttribute('data-id') || el.id;
        if (id) queryParams.append('track_id', id);
    });
    queryParams.append('limit', 10);

    const url = `http://127.0.0.1:8000/recommendations/multi?${queryParams.toString()}`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`Erreur HTTP: ${response.status}`);

        const data = await response.json();
        const reco = data.results || data;

    } catch (error) {
        console.error("Erreur lors de la récupération des recommandations :", error);
        displayElement.innerHTML = "<p>Erreur lors du chargement des recommandations.</p>";
    }
}*/

/* Bouton Reset: Vide les listes */
function Reset() {

    $('#selected-genres-list').empty();
    $('#selected-artists-list').empty();
    $('#selected-tracks-list').empty();
    console.log("Listes réinitialisées !");
}

/* Activation des fonctions */
$(document).ready(function() {
    chargerGenres();
    chargerArtists();
    chargerMusiques();
    //Sauvegarde();
});


/****************************************
 *********** C A R R O U S E L **********
 ****************************************/
function moveCarousel(container, album_index, slideWidth) {
    const gap = parseFloat(getComputedStyle(container).gap);
    console.log("gap",gap)
    const centerOffset = Math.floor(3 / 2);

    // const styles = getComputedStyle(container);
    // const gap = parseFloat(styles.gap); offsetWidth

    // var offset = -(album_index * (slideWidth + gap));
    var offset = album_index * (slideWidth + gap);
    // -(album_index - centerOffset) * (slideWidth + gap);
    container.style.transform = `translateX(${offset}px)`;

    // console.log("slide width",slideWidth)
    console.log("transform:", `translateX(-${offset}px)`);
}

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

        console.log(new_left, currentIndex, new_right); // 🔥 5 6 0 ici

        carrousel_slides.forEach(slide =>
            slide.classList.remove("active")
        );

        carrousel_slides[track_index].classList.add("active");
        carrousel_slides[new_left].classList.add("active");
        carrousel_slides[new_right].classList.add("active");
    })
})