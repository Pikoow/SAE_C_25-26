// Function pour afficher des genres sur la Page Préferences
async function chargerGenres() {
    const selectElement = document.getElementById("genre");
    
    if (!selectElement) {
        return;
    }

    console.log("Tentative de chargement des genres...");

    try {
        const response = await fetch("http://127.0.0.1:8000/genres");
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP : ${response.status}`);
        }

        const data = await response.json();
        const genres = data.results || data;
        selectElement.innerHTML = '<option value="">-- Choisissez un genre --</option>';

        if (Array.isArray(genres)) {
            genres.forEach(genre => {
                const option = document.createElement("option");
                const titre = genre.genre_title || "Sans titre";
                option.value = genre.genre_id || genre.id;
                option.textContent = `${titre}`;
                selectElement.appendChild(option);
            });
            console.log("Liste remplie avec succès !");
        } else {
            console.error("Le format des données n'est pas un tableau", artists);
        }

    } catch (error) {
        console.error("Erreur lors du fetch :", error);
        selectElement.innerHTML = '<option>Erreur de chargement</option>';
    }
}

// Function pour afficher des artistes sur la Page Préferences
async function chargerArtists() {
    const selectElement = document.getElementById("artistes");
    
    if (!selectElement) {
        return;
    }

    console.log("Tentative de chargement des artistes...");

    try {
        const response = await fetch("http://127.0.0.1:8000/artists");
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP : ${response.status}`);
        }

        const data = await response.json();
        const artists = data.results || data;
        selectElement.innerHTML = '<option value="">-- Choisissez un artiste --</option>';

        if (Array.isArray(artists)) {
            artists.forEach(artist => {
                const option = document.createElement("option");
                const titre = artist.artist_name || "Sans titre";
                option.value = artist.artist_id || artist.id;
                option.textContent = `${titre}`;
                selectElement.appendChild(option);
            });
            console.log("Liste remplie avec succès !");
        } else {
            console.error("Le format des données n'est pas un tableau", artists);
        }

    } catch (error) {
        console.error("Erreur lors du fetch :", error);
        selectElement.innerHTML = '<option>Erreur de chargement</option>';
    }
}

// Function pour afficher des musiques sur la Page Préferences
async function chargerMusiques() {
    const selectElement = document.getElementById("musique");
    
    if (!selectElement) {
        return;
    }

    console.log("Tentative de chargement des musiques...");

    try {
        const response = await fetch("http://127.0.0.1:8000/tracks");
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP : ${response.status}`);
        }

        const data = await response.json();
        const tracks = data.results || data;
        selectElement.innerHTML = '<option value="">-- Choisissez une musique --</option>';

        if (Array.isArray(tracks)) {
            tracks.forEach(track => {
                const option = document.createElement("option");
                const titre = track.track_title || "Sans titre";
                
                option.value = titre;
                option.textContent = `${titre}`;
                selectElement.appendChild(option);
            });
            console.log("Liste remplie avec succès !");
        } else {
            console.error("Le format des données n'est pas un tableau", tracks);
        }

    } catch (error) {
        console.error("Erreur lors du fetch :", error);
        selectElement.innerHTML = '<option>Erreur de chargement</option>';
    }
}

chargerGenres();
chargerArtists();
chargerMusiques();