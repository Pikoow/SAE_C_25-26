document.getElementById("load").addEventListener("click", async () => {
  const result = document.getElementById("result");
  result.innerHTML = "";

  try {
    const response = await fetch("http://127.0.0.1:8000/tracks");
    if (!response.ok) throw new Error(`HTTP error ${response.status}`);

    const data = await response.json();
    console.log("data reçue :", data);

    // Récupérer le tableau dans 'results'
    const tracks = data.results || [];

    if (tracks.length === 0) {
      result.innerHTML = "<p>Aucune piste disponible</p>";
      return;
    }

    // Afficher toutes les pistes
    tracks.forEach(track => {
      result.innerHTML += `
        <div style="margin-bottom: 10px; padding: 5px; border-bottom: 1px solid #ccc;">
          <h2>${track.track_title || 'Titre inconnu'}</h2>
          <p>Artiste : ${track.artist_name || 'Inconnu'}</p>
          <p>Durée : ${track.track_duration ? track.track_duration + ' sec' : 'Inconnue'}</p>
          <p>Album : ${track.album_title || 'Inconnu'}</p>
        </div>
      `;
    });

  } catch (error) {
    console.error("Erreur fetch :", error);
    result.innerHTML = "<p>Impossible de charger les pistes.</p>";
  }
});
