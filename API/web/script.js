function ajouterElementSelectionne(nom, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const dejaPresent = Array.from(container.querySelectorAll('.badge-item span'))
                             .some(span => span.textContent === nom);
    if (dejaPresent) return;

    // Apparation des élements
    const badge = document.createElement("div");
    badge.className = "badge-item";
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
                source: listeGenres,
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
                source: listeArtistes,
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
            const listeMusiques = tracks.map(t => t.track_title || "Sans titre");

            $(inputElement).autocomplete({
                source: listeMusiques,
                minLength: 1,
                select: function(event, ui) {
                    ajouterElementSelectionne(ui.item.value, "selected-tracks-list");
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

/* Activation des fonctions */
$(document).ready(function() {
    console.log("DOM et jQuery prêts, chargement des données...");
    chargerGenres();
    chargerArtists();
    chargerMusiques();
});