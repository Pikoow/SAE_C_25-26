function ajouterElementSelectionne(nom, containerId, idElement) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (document.getElementById(`item-${idElement}`)) {
        console.warn("Cet élément est déjà sélectionné");
        return;
    }

    const badge = document.createElement("div");
    badge.className = "badge-item";
    
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
            const listeGenres = genres.map(g => g.genre_title || "Sans titre");

            $(inputElement).autocomplete({
                source: function(request, response) {
                    const term = request.term.toLowerCase();
                    const matches = listeGenres.filter(item => item.toLowerCase().includes(term)).slice(0,15);
                    response(matches);
                },
                minLength: 1,
                select: function(event, ui) {
                    ajouterElementSelectionne(ui.item.value, "selected-genres-list");
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
        const response = await fetch("http://127.0.0.1:8000/artists");
        const data = await response.json();
        const artists = data.results || data;

        if (Array.isArray(artists)) {
            const listeArtistes = artists.map(a => a.artist_name || "Sans titre");

            $(inputElement).autocomplete({
                source: function(request, response) {
                    const term = request.term.toLowerCase();
                    const matches = listeArtistes.filter(item => item.toLowerCase().includes(term)).slice(0,15);
                    response(matches);
                },
                minLength: 1,
                select: function(event, ui) {
                    ajouterElementSelectionne(ui.item.value, "selected-artists-list");
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
        const response = await fetch("http://127.0.0.1:8000/tracks");
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
/*
async function Sauvegarde(params) {
    
    const btnSave = document.querySelector("#btn-save");

}
*/
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
});


/****************************************
 *********** C A R R O U S E L **********
 ****************************************/


const carrousel_buttons = document.querySelectorAll(".carrousel-button");
const carrousel_slides = document.querySelectorAll(".carrousel-slide");
// console.log(carrousel_buttons,carrousel_slides)
let currentIndex = 3

carrousel_buttons.forEach((carrBut) => {
    carrBut.addEventListener('click', (e) => {
        
        const direction = e.target.id === 'next' ? 1 : -1;
        const total = carrousel_slides.length;

        currentIndex = (currentIndex + direction + total) % total;

        const new_left  = (currentIndex - 1 + total) % total;
        const new_right = (currentIndex + 1) % total;

        console.log(new_left, currentIndex, new_right); // 🔥 5 6 0 ici

        carrousel_slides.forEach(slide =>
            slide.classList.remove("active")
        );

        carrousel_slides[currentIndex].classList.add("active");
        carrousel_slides[new_left].classList.add("active");
        carrousel_slides[new_right].classList.add("active");
    })
})