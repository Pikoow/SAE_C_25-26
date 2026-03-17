// header-ui.js
document.addEventListener("DOMContentLoaded", () => {
    updateHeaderDisplay();
});

function updateHeaderDisplay() {
    // 1. Lire les infos
    const userId = localStorage.getItem("userId");
    const userName = localStorage.getItem("userName");
    const userRole = localStorage.getItem("userRole");

    // 2. Sélectionner les éléments
    const authButtons = document.getElementById("auth-buttons");
    const authButtonsDisplay = document.getElementById("auth-buttons-display");
    const userMenu = document.getElementById("user-menu");
    const userNameDisplay = document.getElementById("user-name-display");

    // 3. Appliquer les classes CSS
    if (userId) {
        // --- MODE CONNECTÉ ---
        if (authButtons) authButtons.classList.add("hidden");
        if (authButtonsDisplay) authButtonsDisplay.classList.add("hidden");
        if (userMenu) userMenu.classList.remove("hidden");

        // Mettre le prénom dans le bouton
        if (userName && userNameDisplay) {
            userNameDisplay.innerHTML = `${userName} &nbsp; <span style="display: inline-block; transform: translateY(-1px);">▾</span>`;
        }

        // --- ADMIN LINK ---
        const dropdownContent = userMenu?.querySelector(".user-dropdown-content");
        if (dropdownContent && (userRole === "admin" || userRole === "super_admin")) {
            // Vérifier si le lien admin existe déjà
            if (!dropdownContent.querySelector(".admin-link")) {
                const adminLink = document.createElement("a");
                adminLink.href = "admin.html";
                adminLink.className = "admin-link";
                adminLink.innerHTML = 'Administration';
                adminLink.style.color = "#ed7a26";
                adminLink.style.fontWeight = "600";
                // Insérer avant le lien "Mon profil"
                dropdownContent.insertBefore(adminLink, dropdownContent.firstChild);
            }
        }
    } else {
        // --- MODE DÉCONNECTÉ ---
        if (authButtons) authButtons.classList.remove("hidden");
        if (authButtonsDisplay) authButtonsDisplay.classList.remove("hidden");
        if (userMenu) userMenu.classList.add("hidden");
    }
}