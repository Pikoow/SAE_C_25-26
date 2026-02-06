function ajouterElementSelectionne(nom, containerId, idElement) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (document.getElementById(`${idElement}`)) {
        console.warn("Cet élément est déjà sélectionné");
        return;
    }

    const badge = document.createElement("div");
    badge.className = "badge-item";
    console.log(idElement);
    badge.id = `${idElement}`; 
    badge.title = "Cliquez pour supprimer";
    badge.innerHTML = `<span>${nom}</span>`;

    badge.addEventListener("click", function() {
        this.style.transform = "scale(0)";
        this.style.opacity = "0";
        setTimeout(() => this.remove(), 200);
    });

    container.appendChild(badge);
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
            
            console.log("Autocomplete Genres configuré avec succès !");
        }
    } catch (error) {
        console.error("Erreur lors du chargement des genres :", error);
    }
}

// Fonction pour l'Autocomplete des Artistes
async function chargerArtists() {
    const inputElement = document.getElementById("artistes");
    if (!inputElement) return;

    try {
        const response = await fetch("http://127.0.0.1:8000/artists?limit=5000");
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
    if (!inputElement) return;

    try {
        const response = await fetch("http://127.0.0.1:8000/tracks?limit=5000");
        const data = await response.json();
        const tracks = data.results || data;
        
        if (Array.isArray(tracks)) {
            const listeMusiques = tracks.map(t => ({
                label : t.track_title || "Sans titre",
                value : t.track_title || "Sans titre",
                id : t.track_id
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
            console.log("Autocomplete Musiques prêt !");
        }
    } catch (error) {
        console.error("Erreur Musiques :", error);
    }
}

async function Sauvegarde() {
    const elements = document.querySelectorAll('.badge-item');
    if (elements.length === 0) {
        console.warn("Aucun .badge-item trouvé.");
        return;
    }
    const queryParams = new URLSearchParams();
    elements.forEach(el => {
        if (el.id) {
            queryParams.append('track_id', el.id);
        }
    });
    queryParams.append('limit', 5);
    const url = `http://127.0.0.1:8000/recommendations/multi?${queryParams.toString()}`;
    console.log("Appel API :", url);
    try {

        const response = await fetch(url);
        if (!response.ok) {
            const errorDetail = await response.json();
            throw new Error(`Erreur ${response.status}: ${errorDetail.detail}`);
        }

        const data = await response.json();
        const reco = data.results || [];
        console.log("Musiques similaires trouvées :", reco);
        
    } catch (error) {
        console.error("Erreur lors de la récupération :", error);
    }
}

/* Bouton Reset: Vide les listes */
function Reset() {

    $('#selected-genres-list').empty();
    $('#selected-artists-list').empty();
    $('#selected-tracks-list').empty();
    console.log("Listes réinitialisées !");
}

/* Activation des fonctions */
$(document).ready(function() {
    console.log("DOM et jQuery prêts, chargement des données...");
    chargerGenres();
    chargerArtists();
    chargerMusiques();
    Sauvegarde();
});


/****************************************
 *********** C A R R O U S E L **********
 ****************************************/


const carrousel_buttons = document.querySelectorAll(".carrousel-button");
const carrousel_slides = document.querySelectorAll(".carrousel-slide");
// console.log(carrousel_buttons,carrousel_slides)

carrousel_buttons.forEach((carrBut) => {
    carrBut.addEventListener('click', (e) => {
        // console.log(e.target.id)
        const get_next_slide = e.target.id === 'next' ? 1 :-1;
        const slide_actives = document.querySelectorAll(".active");
        let slide_active = slide_actives[1];
        // console.log(slide_active)
        new_active = get_next_slide + [...carrousel_slides].indexOf(slide_active);
        // new_active = (new_active + carrousel_slides.length) % carrousel_slides.length
        
        
        if (new_active < 0) new_active = [...carrousel_slides].length -1
        if (new_active >= [...carrousel_slides].length) new_active = 0

        new_right  = (new_active + 1) % carrousel_slides.length
        new_left   = (new_active - 1 + carrousel_slides.length) % carrousel_slides.length
        
        // console.log("pre",new_left,new_active,new_right)
        
        // if (new_right < 0) new_right = [...carrousel_slides].length -1
        // if (new_right >= [...carrousel_slides].length) new_right = 0
        
        // if (new_left < 0) new_left = [...carrousel_slides].length -1
        // if (new_left >= [...carrousel_slides].length) new_left = 0
        

        console.log(new_left,new_active,new_right)

        carrousel_slides.forEach(slide =>
            slide.classList.remove("active")
        );

        carrousel_slides[new_active].classList.add("active");
        carrousel_slides[new_right].classList.add("active");
        carrousel_slides[new_left].classList.add("active");
    })
})