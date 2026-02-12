// header-ui.js
document.addEventListener("DOMContentLoaded", () => {
    updateHeaderDisplay();
});

function updateHeaderDisplay() {
    // 1. Lire les infos
    const userId = localStorage.getItem("userId");
    const userName = localStorage.getItem("userName");

    // 2. Sélectionner les éléments
    const authButtons = document.getElementById("auth-buttons");
    const userMenu = document.getElementById("user-menu");
    const userNameDisplay = document.getElementById("user-name-display");

    // 3. Appliquer les classes CSS
    if (userId) {
        // --- MODE CONNECTÉ ---
        if (authButtons) authButtons.classList.add("hidden");
        if (userMenu) userMenu.classList.remove("hidden");
        
        // Mettre le prénom dans le bouton
        if (userName && userNameDisplay) {
            userNameDisplay.innerHTML = `${userName} ▾`;
        }
    } else {
        // --- MODE DÉCONNECTÉ ---
        if (authButtons) authButtons.classList.remove("hidden");
        if (userMenu) userMenu.classList.add("hidden");
    }
}