const popup = document.getElementById("albumPopup");
const closeBtn = document.querySelector(".album-close");

const popupTitle = document.getElementById("popupTitle");
const popupArtist = document.getElementById("popupArtist");
const popupTracksCount = document.getElementById("popupTracksCount");
const popupTracksList = document.getElementById("popupTracksList");

// Click sur un album
document.addEventListener("click", function (e) {
  const card = e.target.closest(".album-card");

  if (card) {
    const albumId = card.dataset.id;
    openAlbumPopup(albumId);
  }
});

async function openAlbumPopup(albumId) {
  try {
    const response = await fetch(`http://127.0.0.1:8000/albums/${albumId}/tracks`);    
    const data = await response.json();

    // IMPORTANT : on récupère les bons niveaux
    console.log("data",data);
    const album = data.album;
    const tracks = data.tracks;
    const artists = data.artists;

    // Remplir la popup
    popupTitle.textContent = album.album_title;
    popupArtist.textContent = artists.join(", ");
    popupTracksCount.textContent = album.album_tracks;

    popupTracksList.innerHTML = "";

    tracks.forEach(track => {
      const li = document.createElement("li");

      // convertir durée secondes → mm:ss
      const minutes = Math.floor(track.track_duration / 60);
      const seconds = track.track_duration % 60;
      const formattedDuration =
        `${minutes}:${seconds.toString().padStart(2, "0")}`;

      li.textContent = `${track.track_title} (${formattedDuration})`;

      popupTracksList.appendChild(li);
    });

    popup.classList.remove("hidden");

  } catch (error) {
    console.error("Erreur fetch album :", error);
  }
}
