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
                adminLink.style.color = "var(--orange)";
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

// APRÈS — attend que le DOM soit prêt
document.addEventListener('DOMContentLoaded', function() {
    (function() {
        const THEME_KEY = 'muse-theme';
        const SWATCH_COLORS = {
            orange: 'rgb(237,122,38)',
            violet: 'rgb(124,77,211)',
            vert:   'rgb(39,174,96)',
            bleu:   'rgb(41, 128, 185)'
        };

        const toggleBtn = document.getElementById('themeBtnToggle');
        const panel     = document.getElementById('themePanel');
        const dot       = document.getElementById('themeBtnDot');
        const options   = document.querySelectorAll('.theme-option');

        if (!toggleBtn) return; // sécurité si la page n'a pas le bouton

        applyTheme(localStorage.getItem(THEME_KEY) || 'orange', false);

        toggleBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isOpen = panel.classList.contains('visible');
            panel.classList.toggle('visible', !isOpen);
            toggleBtn.setAttribute('aria-expanded', String(!isOpen));
        });

        document.addEventListener('click', function(e) {
            if (!e.target.closest('.theme-switcher-wrapper')) {
                panel.classList.remove('visible');
                toggleBtn.setAttribute('aria-expanded', 'false');
            }
        });

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                panel.classList.remove('visible');
                toggleBtn.setAttribute('aria-expanded', 'false');
            }
        });

        options.forEach(function(btn) {
            btn.addEventListener('click', function() {
                applyTheme(this.dataset.theme, true);
                panel.classList.remove('visible');
                toggleBtn.setAttribute('aria-expanded', 'false');
            });
        });

        function applyTheme(theme, save) {
            if (theme === 'orange') {
                document.documentElement.removeAttribute('data-theme');
            } else {
                document.documentElement.setAttribute('data-theme', theme);
            }
            dot.style.backgroundColor = SWATCH_COLORS[theme] || SWATCH_COLORS.orange;
            options.forEach(function(btn) {
                const active = btn.dataset.theme === theme;
                btn.classList.toggle('active', active);
                btn.setAttribute('aria-selected', String(active));
            });
            if (save) localStorage.setItem(THEME_KEY, theme);
        }
    })();
});