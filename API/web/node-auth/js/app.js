// app.js
document.addEventListener("DOMContentLoaded", () => {
    
    const logoutBtn = document.getElementById("logoutBtn");

    // On vérifie que le bouton existe (pour éviter les erreurs sur les pages sans header)
    if (logoutBtn) {
        logoutBtn.addEventListener("click", async (e) => {
            e.preventDefault(); // Empêche le lien de mettre un # dans l'url

            try {
                // Appel à votre route Node.js
                const res = await fetch("http://localhost:3000/logout", {
                    method: "POST",
                    credentials: "include"
                });

                const result = await res.json();

                if (result.success) {
                    // 1. Nettoyage technique
                    localStorage.removeItem("userId");
                    localStorage.removeItem("userName");
                    localStorage.clear();

                    // 2. Redirection
                    // window.location.href renvoie à la racine ou page d'accueil
                    window.location.href = "accueil.html"; 
                } else {
                    console.error("Erreur serveur:", result.error);
                    alert("Erreur lors de la déconnexion");
                }
            } catch (err) {
                console.error("Erreur réseau:", err);
                // Optionnel : Forcer la déconnexion locale même si le serveur ne répond pas
                // localStorage.clear();
                // window.location.href = "accueil.html";
            }
        });
    }
});