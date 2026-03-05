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

        // --- ADMIN LINK ---
        const dropdownContent = userMenu?.querySelector(".user-dropdown-content");
        if (dropdownContent && (userRole === "admin" || userRole === "super_admin")) {
            // Vérifier si le lien admin existe déjà
            if (!dropdownContent.querySelector(".admin-link")) {
                const adminLink = document.createElement("a");
                adminLink.href = "admin.html";
                adminLink.className = "admin-link";
                adminLink.innerHTML = '<svg style="width:14px;height:14px;vertical-align:middle;margin-right:5px" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>Administration';
                adminLink.style.color = "#ed7a26";
                adminLink.style.fontWeight = "600";
                // Insérer avant le lien "Mon profil"
                dropdownContent.insertBefore(adminLink, dropdownContent.firstChild);
            }
        }
    } else {
        // --- MODE DÉCONNECTÉ ---
        if (authButtons) authButtons.classList.remove("hidden");
        if (userMenu) userMenu.classList.add("hidden");
    }
}