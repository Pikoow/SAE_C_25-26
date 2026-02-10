// Fonction Gestion des elements des liste(Ajouter/Supression)
function ajouterElementSelectionne(nom, containerId, idElement) {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (document.getElementById(idElement)) {
        console.warn("Cet élément est déjà sélectionné");
        return;
    }

    const badge = document.createElement("div");
    badge.className = "badge-item";
    badge.id = idElement; 
    badge.title = "Cliquez pour supprimer";
    badge.innerHTML = `<span>${nom}</span>`;

    badge.addEventListener("click", function() {
        this.style.transform = "scale(0)";
        this.style.opacity = "0";
        
        setTimeout(() => {
            this.remove();
            
            if (containerId === "selected-artists-list") {
                const resteDesArtistes = container.querySelectorAll('.badge-item').length;
                
                if (resteDesArtistes === 0) {
                    $('#selected-tracks-list').empty();
                } else {
                    chargerMusiques();
                }
            }
        }, 200);
    });

    container.appendChild(badge);

    if(containerId === "selected-genres-list") {
        chargerArtists();
    }

    if (containerId === "selected-artists-list") {
        chargerMusiques();
    }

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
    const elements = document.querySelectorAll('.badge-item');

    if (!inputElement) return;
    const genresNames = Array.from(elements)
        .map(el => el.textContent.trim())
        .filter(name => name);

    const genre1 = genresNames[0] || "None"; 
    const genre2 = genresNames[1] || genre1;
    const url = `http://127.0.0.1:8000/ternaire/${genre1}/${genre2}`;
    console.log("URL construite :", url);
    
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
    const artistContainer = document.getElementById("selected-artists-list"); 
    if (!inputElement || !artistContainer) return;

    const elements = artistContainer.querySelectorAll('.badge-item');

    const artistIds = Array.from(elements)
        .map(el => el.getAttribute('data-id') || el.id)
        .filter(id => id);

    const url = `http://127.0.0.1:8000/artists/${artistIds}/tracks`;
    console.log("URL construite :", url);
    try {
        const response = await fetch(url);
        const data = await response.json();
        const tracks = data.tracks || data.results || data;

        console.log("Tableau final extrait :", tracks);

        if (Array.isArray(tracks)) {
            const listeMusiques = tracks.map(t => ({
                label: t.track_title || "Sans titre",
                value: t.track_title || "Sans titre",
                id: t.track_id
            }));

            if ($(inputElement).data("ui-autocomplete")) {
                $(inputElement).autocomplete("destroy");
            }

            $(inputElement).autocomplete({
                source: function(request, response) {
                    const term = request.term.toLowerCase();
                    const matches = listeMusiques
                        .filter(item => item.label.toLowerCase().includes(term))
                        .slice(0, 15);
                    response(matches);
                },
                minLength: 1,
                select: function(event, ui) {
                    ajouterElementSelectionne(ui.item.value, "selected-tracks-list", ui.item.id);
                    $(this).val("");
                    return false;
                }
            });
            console.log("Autocomplete Musiques mis à jour avec", listeMusiques.length, "titres.");
        }
    } catch (error) {
        console.error("Erreur Musiques :", error);
    }
}

async function Sauvegarde() {
    const elements = document.querySelectorAll('.badge-item');
    
    if (elements.length === 0) {
        return [];
    }

    const queryParams = new URLSearchParams();
    elements.forEach(el => {
        if (el.id) queryParams.append('track_id', el.id);
    });
    queryParams.append('limit', 5);

    const url = `http://127.0.0.1:8000/recommendations/multi?${queryParams.toString()}`;

    try {
        const response = await fetch(url);
        
        if (!response.ok) {
            const errorDetail = await response.json();
            throw new Error(`Erreur ${response.status}: ${errorDetail.detail}`);
        }

        const data = await response.json();
        const reco = data.results || [];
        console.log(reco)
        return reco; 

    } catch (error) {
        console.error("Erreur lors de la récupération :", error);
        throw error;
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
    chargerGenres();
    Sauvegarde();
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