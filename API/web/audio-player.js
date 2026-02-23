class AudioPlayer {
    constructor() {
        this.audio = new Audio();
        this.currentTrack = null;
        this.isPlaying = false;
        this.volume = 0.7;
        this.audio.volume = this.volume;

        // Queue system
        this.queue = [];
        this.queueIndex = -1;
        this.onTrackEnd = null; // callback when track finishes
        this.onNext = null; // callback for skip next
        this.onPrev = null; // callback for skip prev
        this.source = null; // { type: 'playlist'|'album'|'artist', id, name }

        this.createPlayerUI();
        this.setupEventListeners();
        this.restoreState();

        // Save state before leaving page
        window.addEventListener('beforeunload', () => this.saveState());
    }

    createPlayerUI() {
        this.playerContainer = document.createElement('div');
        this.playerContainer.id = 'audio-player-container';
        this.playerContainer.innerHTML = `
            <div class="player-left">
                <div class="track-title" id="current-track-title">Aucune musique</div>
                <div class="artist-name" id="current-artist-name">Sélectionnez une piste</div>
                <div class="player-source-tag" id="player-source-tag" style="display:none;"></div>
            </div>
            
            <div class="player-center">
                <button id="stop-btn" class="stop-btn" disabled>
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <rect x="6" y="6" width="12" height="12"/>
                    </svg>
                </button>
                <button id="prev-btn" class="skip-btn" title="Précédent">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/>
                    </svg>
                </button>
                <button id="play-pause-btn" class="play-btn" disabled>
                    <svg class="play-icon" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M8 5v14l11-7z"/>
                    </svg>
                    <svg class="pause-icon" viewBox="0 0 24 24" fill="currentColor" style="display: none;">
                        <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z"/>
                    </svg>
                </button>
                <button id="next-btn" class="skip-btn" title="Suivant">
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/>
                    </svg>
                </button>
            </div>
            
            <div class="player-right">
                <button class="player-add-playlist-btn" id="player-add-playlist-btn" title="Ajouter à une playlist" disabled>+</button>
                <span class="time-current">0:00</span>
                <span class="time-separator">/</span>
                <span class="time-total">0:00</span>
            </div>
            
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-fill"></div>
                </div>
                <input type="range" id="progress-input" min="0" max="100" value="0" disabled>
            </div>
        `;

        const style = document.createElement('style');
        style.textContent = `
            #audio-player-container {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                height: 80px;
                background: rgb(0, 0, 0);
                color: white;
                padding: 0 40px;
                z-index: 7000;
                display: grid;
                grid-template-columns: 1fr auto 1fr;
                align-items: center;
                gap: 30px;
                box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.2);
                font-family: 'Outfit', sans-serif;
            }

            .player-left {
                display: flex;
                flex-direction: column;
                gap: 4px;
                justify-self: start;
            }

            .track-title {
                font-weight: 600;
                font-size: 16px;
                color: white;
            }

            .artist-name {
                font-size: 14px;
                color: rgba(255, 255, 255, 0.6);
            }

            .player-source-tag {
                display: inline-flex;
                align-items: center;
                gap: 4px;
                font-size: 11px;
                color: var(--orange, #e67e22);
                cursor: pointer;
                opacity: 0.85;
                transition: opacity 0.2s;
                max-width: 200px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .player-source-tag:hover {
                opacity: 1;
                text-decoration: underline;
            }

            .player-center {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 15px;
            }

            .stop-btn {
                width: 40px;
                height: 40px;
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.1);
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }

            .stop-btn:hover:not(:disabled) {
                background: rgba(255, 255, 255, 0.2);
            }

            .stop-btn:disabled {
                opacity: 0.3;
                cursor: not-allowed;
            }

            .stop-btn svg {
                width: 18px;
                height: 18px;
                color: white;
            }

            .skip-btn {
                width: 36px;
                height: 36px;
                border-radius: 50%;
                background: transparent;
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                color: rgba(255,255,255,0.7);
            }

            .skip-btn:hover {
                color: white;
                background: rgba(255,255,255,0.1);
            }

            .skip-btn svg {
                width: 20px;
                height: 20px;
            }

            .play-btn {
                width: 50px;
                height: 50px;
                border-radius: 50%;
                background: rgb(237, 122, 38);
                border: none;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
            }

            .play-btn:hover:not(:disabled) {
                background: rgb(253, 114, 8);
                transform: scale(1.05);
            }

            .play-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .play-btn svg {
                width: 24px;
                height: 24px;
                color: white;
            }

            .player-right {
                display: flex;
                align-items: center;
                gap: 8px;
                justify-self: end;
                font-size: 13px;
                color: rgba(255, 255, 255, 0.7);
                font-variant-numeric: tabular-nums;
            }

            .player-add-playlist-btn {
                width: 32px;
                height: 32px;
                border-radius: 50%;
                border: 2px solid rgba(255,255,255,0.3);
                background: transparent;
                color: rgba(255,255,255,0.6);
                font-size: 18px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s ease;
                padding: 0;
                line-height: 1;
                margin-right: 6px;
            }

            .player-add-playlist-btn:hover:not(:disabled) {
                border-color: #ed7a26;
                color: #ed7a26;
                transform: scale(1.1);
            }

            .player-add-playlist-btn:disabled {
                opacity: 0.2;
                cursor: not-allowed;
            }

            .player-add-playlist-btn.added {
                border-color: #27ae60;
                color: #27ae60;
            }

            /* Player playlist dropdown */
            .player-playlist-dropdown {
                position: fixed;
                background: white;
                border-radius: 10px;
                box-shadow: 0 8px 30px rgba(0,0,0,0.25);
                z-index: 8000;
                min-width: 230px;
                max-height: 240px;
                overflow-y: auto;
                padding: 6px 0;
                display: none;
                font-family: 'Outfit', sans-serif;
            }

            .player-playlist-dropdown.visible {
                display: block;
            }

            .player-playlist-dropdown .ppd-title {
                font-size: 11px;
                font-weight: 600;
                color: #95a5a6;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                padding: 8px 14px 4px;
                margin: 0;
            }

            .player-playlist-dropdown .ppd-item {
                padding: 9px 14px;
                cursor: pointer;
                font-size: 13px;
                color: #2c3e50;
                transition: background 0.15s;
                display: flex;
                align-items: center;
                gap: 8px;
            }

            .player-playlist-dropdown .ppd-item:hover {
                background: #fff3e6;
                color: #ed7a26;
            }

            .player-playlist-dropdown .ppd-item .ppd-icon {
                font-size: 14px;
            }

            .player-playlist-dropdown .ppd-empty {
                padding: 12px 14px;
                font-size: 12px;
                color: #bdc3c7;
                text-align: center;
            }

            .player-playlist-dropdown .ppd-login {
                padding: 12px 14px;
                font-size: 12px;
                color: #ed7a26;
                text-align: center;
            }

            .player-playlist-dropdown .ppd-login a {
                color: #ed7a26;
                font-weight: 600;
                text-decoration: none;
            }

            .player-playlist-dropdown .ppd-quick-create {
                padding: 10px 14px;
                border-top: 1px solid #f0f0f0;
            }

            .player-playlist-dropdown .ppd-quick-create input {
                width: 100%;
                padding: 7px 10px;
                border: 1.5px solid #ddd;
                border-radius: 6px;
                font-size: 12px;
                font-family: 'Outfit', sans-serif;
                outline: none;
                transition: border-color 0.2s;
                box-sizing: border-box;
                margin-bottom: 6px;
            }

            .player-playlist-dropdown .ppd-quick-create input:focus {
                border-color: #ed7a26;
            }

            .player-playlist-dropdown .ppd-quick-create button {
                width: 100%;
                padding: 7px;
                background: #ed7a26;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Outfit', sans-serif;
                cursor: pointer;
                transition: background 0.2s;
            }

            .player-playlist-dropdown .ppd-quick-create button:hover {
                background: #d36a1a;
            }

            .player-playlist-dropdown .ppd-quick-create button:disabled {
                background: #ccc;
                cursor: not-allowed;
            }

            .time-separator {
                color: rgba(255, 255, 255, 0.4);
            }

            @keyframes playerNotifAnim {
                0% { opacity: 0; transform: translateX(-50%) translateY(20px); }
                15% { opacity: 1; transform: translateX(-50%) translateY(0); }
                85% { opacity: 1; transform: translateX(-50%) translateY(0); }
                100% { opacity: 0; transform: translateX(-50%) translateY(-10px); }
            }

            .progress-container {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
            }

            .progress-bar {
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.1);
                position: relative;
                overflow: hidden;
            }

            .progress-fill {
                height: 100%;
                background: rgb(237, 122, 38);
                width: 0%;
                transition: width 0.1s linear;
            }

            #progress-input {
                position: absolute;
                top: -6px;
                left: 0;
                width: 100%;
                height: 16px;
                -webkit-appearance: none;
                background: transparent;
                cursor: pointer;
                outline: none;
            }

            #progress-input::-webkit-slider-thumb {
                -webkit-appearance: none;
                width: 0;
                height: 0;
                transition: all 0.2s ease;
            }

            #progress-input:hover::-webkit-slider-thumb {
                width: 14px;
                height: 14px;
                border-radius: 50%;
                background: white;
                cursor: pointer;
            }

            #progress-input:disabled {
                cursor: default;
            }

            .track-card.playing {
                border-left: 4px solid rgb(237, 122, 38);
                background: rgba(237, 122, 38, 0.1) !important;
            }

            /* Responsive */
            @media (max-width: 768px) {
                #audio-player-container {
                    padding: 0 20px;
                    grid-template-columns: 1fr auto auto;
                    gap: 15px;
                }
                
                .player-left {
                    min-width: 0;
                }
                
                .track-title {
                    font-size: 14px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    max-width: 180px;
                }
                
                .artist-name {
                    font-size: 12px;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    white-space: nowrap;
                    max-width: 180px;
                }
                
                .player-right {
                    font-size: 12px;
                }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(this.playerContainer);

        this.playPauseBtn = document.getElementById('play-pause-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.progressInput = document.getElementById('progress-input');
        this.progressFill = document.getElementById('progress-fill');
        this.timeCurrent = document.querySelector('.time-current');
        this.timeTotal = document.querySelector('.time-total');
        this.trackTitleEl = document.getElementById('current-track-title');
        this.artistNameEl = document.getElementById('current-artist-name');
        this.playIcon = this.playPauseBtn.querySelector('.play-icon');
        this.pauseIcon = this.playPauseBtn.querySelector('.pause-icon');
        this.addPlaylistBtn = document.getElementById('player-add-playlist-btn');
        this.prevBtn = document.getElementById('prev-btn');
        this.nextBtn = document.getElementById('next-btn');
        this.sourceTagEl = document.getElementById('player-source-tag');

        // Source tag click
        this.sourceTagEl.addEventListener('click', (e) => {
            e.stopPropagation();
            if (this.source && typeof window.openPlayerSource === 'function') {
                window.openPlayerSource(this.source.type, this.source.id, this.source.name);
            }
        });

        // Créer le dropdown playlist du player
        this.playlistDropdown = document.createElement('div');
        this.playlistDropdown.className = 'player-playlist-dropdown';
        this.playlistDropdown.id = 'playerPlaylistDropdown';
        document.body.appendChild(this.playlistDropdown);

        // Fermer le dropdown si clic ailleurs
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.player-playlist-dropdown') && !e.target.closest('#player-add-playlist-btn') && !e.target.closest('.ppd-quick-create')) {
                this.playlistDropdown.classList.remove('visible');
            }
        });

        // Clic sur le bouton "+"
        this.addPlaylistBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (!this.currentTrack || !this.currentTrack.trackId) return;
            this.showPlayerPlaylistPicker();
        });
    }

    setupEventListeners() {
        this.playPauseBtn.addEventListener('click', () => {
            if (this.isPlaying) {
                this.pause();
            } else {
                this.play();
            }
        });

        this.stopBtn.addEventListener('click', () => {
            this.stop();
        });

        this.progressInput.addEventListener('input', (e) => {
            const time = (e.target.value / 100) * this.audio.duration;
            this.audio.currentTime = time;
            this.updateProgress();
        });

        this.audio.addEventListener('timeupdate', () => {
            this.updateProgress();
        });

        this.audio.addEventListener('loadedmetadata', () => {
            this.updateTimeDisplay();
            this.progressInput.disabled = false;
        });

        this.audio.addEventListener('ended', () => {
            // If external callback handles it (playlist modal), use that
            if (this.onTrackEnd) {
                this.onTrackEnd();
                return;
            }
            // Otherwise try to play next in queue
            if (!this.playNext()) {
                this.stop();
            }
        });

        this.audio.addEventListener('play', () => {
            this.isPlaying = true;
            this.updatePlayPauseButton();
        });

        this.audio.addEventListener('pause', () => {
            this.isPlaying = false;
            this.updatePlayPauseButton();
        });

        // Skip buttons
        this.prevBtn.addEventListener('click', () => {
            if (this.onPrev) {
                this.onPrev();
            } else {
                this.playPrev();
            }
        });

        this.nextBtn.addEventListener('click', () => {
            if (this.onNext) {
                this.onNext();
            } else {
                this.playNext();
            }
        });
    }

    convertTrackUrl(dbUrl) {
        if (!dbUrl) return '';
        let path = dbUrl.startsWith('music/') ? dbUrl.substring(6) : dbUrl;
        return `https://files.freemusicarchive.org/storage-freemusicarchive-org/music/${path}`;
    }

    playTrack(trackInfo) {
        const { url, title, artist, trackId } = trackInfo;

        if (!url) {
            console.error('No track URL provided');
            return;
        }

        const fullUrl = this.convertTrackUrl(url);

        this.currentTrack = {
            url: fullUrl,
            title: title || 'Titre inconnu',
            artist: artist || 'Artiste inconnu',
            trackId: trackId || null
        };

        this.audio.src = fullUrl;
        this.trackTitleEl.textContent = this.currentTrack.title;
        this.artistNameEl.textContent = this.currentTrack.artist;

        // Activer le bouton playlist si on a un trackId
        if (this.addPlaylistBtn) {
            this.addPlaylistBtn.disabled = !trackId;
        }

        // Clear source if not set externally before this call
        // (source is set via setSource before playTrack)

        this.play();
    }

    setSource(type, id, name) {
        if (!type) {
            this.source = null;
            this.sourceTagEl.style.display = 'none';
            return;
        }
        const icons = { playlist: '📋', album: '💿', artist: '🎤' };
        this.source = { type, id, name };
        this.sourceTagEl.textContent = (icons[type] || '🎵') + ' ' + name;
        this.sourceTagEl.title = 'Ouvrir : ' + name;
        this.sourceTagEl.style.display = 'inline-flex';
    }

    clearSource() {
        this.setSource(null);
    }

    play() {
        if (this.audio.src) {
            this.audio.play();
            this.playPauseBtn.disabled = false;
            this.stopBtn.disabled = false;
        }
    }

    pause() {
        this.audio.pause();
    }

    stop() {
        this.audio.pause();
        this.audio.currentTime = 0;
        this.progressInput.value = 0;
        this.progressFill.style.width = '0%';
        this.timeCurrent.textContent = '0:00';
        this.isPlaying = false;
        this.updatePlayPauseButton();
    }

    updateProgress() {
        if (this.audio.duration) {
            const progress = (this.audio.currentTime / this.audio.duration) * 100;
            this.progressInput.value = progress;
            this.progressFill.style.width = progress + '%';
            this.updateTimeDisplay();
        }
    }

    updateTimeDisplay() {
        const formatTime = (seconds) => {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        };

        this.timeCurrent.textContent = formatTime(this.audio.currentTime || 0);

        if (this.audio.duration && !isNaN(this.audio.duration)) {
            this.timeTotal.textContent = formatTime(this.audio.duration);
        }
    }

    updatePlayPauseButton() {
        if (this.isPlaying) {
            this.playIcon.style.display = 'none';
            this.pauseIcon.style.display = 'block';
        } else {
            this.playIcon.style.display = 'block';
            this.pauseIcon.style.display = 'none';
        }
    }

    // ====== Playlist logic pour le player ======

    async showPlayerPlaylistPicker() {
        const dd = this.playlistDropdown;
        const btn = this.addPlaylistBtn;
        const trackId = this.currentTrack.trackId;

        // Positionner au-dessus du bouton
        const rect = btn.getBoundingClientRect();
        dd.style.bottom = (window.innerHeight - rect.top + 8) + 'px';
        dd.style.right = (window.innerWidth - rect.right) + 'px';
        dd.style.top = 'auto';
        dd.style.left = 'auto';

        dd.innerHTML = '<p class="ppd-title">Chargement...</p>';
        dd.classList.add('visible');

        try {
            const authRes = await fetch('http://localhost:3000/dashboard', { credentials: 'include' });
            const authData = await authRes.json();

            if (authData.error) {
                dd.innerHTML = '<div class="ppd-login"><a href="connexion.html">Connectez-vous</a> pour ajouter à une playlist</div>';
                return;
            }

            const userId = authData.user.user_id || 1;

            const plRes = await fetch(`http://127.0.0.1:8000/users/${userId}/playlists`);
            const playlists = await plRes.json();

            if (!playlists || playlists.length === 0) {
                dd.innerHTML = `
                    <p class="ppd-title">Aucune playlist</p>
                    <div class="ppd-quick-create">
                        <input type="text" id="playerQuickName" placeholder="Nom de la playlist" maxlength="50">
                        <button id="playerQuickCreateBtn">✨ Créer et ajouter</button>
                    </div>
                `;
                setTimeout(() => {
                    const inp = document.getElementById('playerQuickName');
                    if (inp) inp.focus();
                    const createBtn = document.getElementById('playerQuickCreateBtn');
                    if (createBtn) createBtn.addEventListener('click', () => this.playerQuickCreate(userId, trackId));
                }, 50);
                return;
            }

            let html = '<p class="ppd-title">Ajouter à...</p>';
            playlists.forEach(pl => {
                html += `<div class="ppd-item" data-playlist-id="${pl.playlist_id}">
                    <span class="ppd-icon">🎵</span>${this.escapeHtml(pl.playlist_name)}
                </div>`;
            });
            html += '<div style="border-top:1px solid #f0f0f0; margin-top:4px;"></div>';
            html += '<div class="ppd-item ppd-new" style="color:#ed7a26;font-weight:500;"><span class="ppd-icon">➕</span> Nouvelle playlist</div>';
            dd.innerHTML = html;

            // Listeners playlists existantes
            dd.querySelectorAll('.ppd-item:not(.ppd-new)').forEach(item => {
                item.addEventListener('click', async () => {
                    const plId = item.dataset.playlistId;
                    await this.playerAddToPlaylist(plId, trackId);
                    dd.classList.remove('visible');
                });
            });

            // Listener nouvelle playlist
            const newBtn = dd.querySelector('.ppd-new');
            if (newBtn) {
                newBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    dd.innerHTML = `
                        <p class="ppd-title">Nouvelle playlist</p>
                        <div class="ppd-quick-create">
                            <input type="text" id="playerQuickName" placeholder="Nom de la playlist" maxlength="50">
                            <button id="playerQuickCreateBtn">✨ Créer et ajouter</button>
                        </div>
                    `;
                    setTimeout(() => {
                        const inp = document.getElementById('playerQuickName');
                        if (inp) inp.focus();
                        const createBtn = document.getElementById('playerQuickCreateBtn');
                        if (createBtn) createBtn.addEventListener('click', () => this.playerQuickCreate(userId, trackId));
                    }, 50);
                });
            }

        } catch (err) {
            console.error('Player playlist error:', err);
            dd.innerHTML = '<div class="ppd-empty">Erreur de chargement</div>';
        }
    }

    async playerAddToPlaylist(playlistId, trackId) {
        try {
            const getRes = await fetch(`http://127.0.0.1:8000/playlists/${playlistId}`);
            const playlist = await getRes.json();
            const existingIds = (playlist.tracks || []).map(t => t.track_id);

            if (existingIds.includes(parseInt(trackId))) {
                this.playerShowNotif('Déjà dans cette playlist', 'info');
                return;
            }

            existingIds.push(parseInt(trackId));

            const postRes = await fetch(`http://127.0.0.1:8000/playlists/${playlistId}/tracks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ track_ids: existingIds })
            });

            if (postRes.ok) {
                this.addPlaylistBtn.textContent = '✓';
                this.addPlaylistBtn.classList.add('added');
                setTimeout(() => {
                    this.addPlaylistBtn.textContent = '+';
                    this.addPlaylistBtn.classList.remove('added');
                }, 2000);
                this.playerShowNotif('✅ Ajouté à « ' + (playlist.playlist_name || 'la playlist') + ' » !', 'success');
            } else {
                this.playerShowNotif('Erreur lors de l\'ajout', 'error');
            }
        } catch (err) {
            console.error('Player add track error:', err);
            this.playerShowNotif('Erreur lors de l\'ajout', 'error');
        }
    }

    async playerQuickCreate(userId, trackId) {
        const nameInput = document.getElementById('playerQuickName');
        const btn = document.getElementById('playerQuickCreateBtn');
        const name = nameInput ? nameInput.value.trim() : '';

        if (!name) {
            nameInput.style.borderColor = '#e74c3c';
            nameInput.placeholder = 'Entrez un nom !';
            return;
        }

        btn.disabled = true;
        btn.textContent = 'Création...';

        try {
            const res = await fetch('http://127.0.0.1:8000/playlists', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    description: '',
                    user_id: userId,
                    track_ids: [parseInt(trackId)]
                })
            });

            if (res.ok) {
                this.playlistDropdown.classList.remove('visible');
                this.addPlaylistBtn.textContent = '✓';
                this.addPlaylistBtn.classList.add('added');
                setTimeout(() => {
                    this.addPlaylistBtn.textContent = '+';
                    this.addPlaylistBtn.classList.remove('added');
                }, 2000);
                this.playerShowNotif('✅ Playlist « ' + name + ' » créée !', 'success');
            } else {
                this.playerShowNotif('Erreur lors de la création', 'error');
                btn.disabled = false;
                btn.textContent = '✨ Créer et ajouter';
            }
        } catch (err) {
            console.error('Player create playlist error:', err);
            this.playerShowNotif('Erreur lors de la création', 'error');
            btn.disabled = false;
            btn.textContent = '✨ Créer et ajouter';
        }
    }

    playerShowNotif(message, type) {
        const existing = document.querySelector('.player-notif');
        if (existing) existing.remove();

        const notif = document.createElement('div');
        notif.className = 'player-notif';
        notif.textContent = message;
        notif.style.cssText = `
            position: fixed; bottom: 100px; left: 50%; transform: translateX(-50%);
            background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
            color: white; padding: 12px 28px; border-radius: 10px; font-size: 14px;
            font-weight: 500; font-family: 'Outfit', sans-serif; z-index: 10002;
            box-shadow: 0 6px 20px rgba(0,0,0,0.25);
            animation: playerNotifAnim 2.8s ease forwards;
        `;
        document.body.appendChild(notif);
        setTimeout(() => notif.remove(), 3000);
    }

    escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // ---- Queue system ----
    setQueue(tracks, startIndex = 0) {
        this.queue = tracks; // Array of { url, title, artist, trackId }
        this.queueIndex = startIndex;
    }

    playNext() {
        if (this.queue.length === 0) return false;
        this.queueIndex++;
        if (this.queueIndex >= this.queue.length) {
            this.queueIndex = this.queue.length; // past end
            return false;
        }
        this.playTrack(this.queue[this.queueIndex]);
        return true;
    }

    playPrev() {
        if (this.queue.length === 0) return false;
        // If more than 3s in, restart current track
        if (this.audio.currentTime > 3) {
            this.audio.currentTime = 0;
            return true;
        }
        this.queueIndex--;
        if (this.queueIndex < 0) {
            this.queueIndex = 0;
            this.audio.currentTime = 0;
            return true;
        }
        this.playTrack(this.queue[this.queueIndex]);
        return true;
    }

    // ---- Cross-page persistence ----
    saveState() {
        if (!this.currentTrack || !this.audio.src) return;
        const state = {
            track: this.currentTrack,
            currentTime: this.audio.currentTime,
            isPlaying: this.isPlaying,
            queue: this.queue,
            queueIndex: this.queueIndex,
            source: this.source
        };
        try {
            localStorage.setItem('audioPlayerState', JSON.stringify(state));
        } catch (e) { /* ignore */ }
    }

    restoreState() {
        try {
            const raw = localStorage.getItem('audioPlayerState');
            if (!raw) return;
            localStorage.removeItem('audioPlayerState');
            const state = JSON.parse(raw);
            if (!state.track || !state.track.url) return;

            this.currentTrack = state.track;
            this.audio.src = state.track.url;
            this.trackTitleEl.textContent = state.track.title || 'Titre inconnu';
            this.artistNameEl.textContent = state.track.artist || 'Artiste inconnu';
            if (this.addPlaylistBtn) {
                this.addPlaylistBtn.disabled = !state.track.trackId;
            }

            // Restore queue
            if (state.queue && state.queue.length > 0) {
                this.queue = state.queue;
                this.queueIndex = state.queueIndex || 0;
            }

            // Restore source tag
            if (state.source) {
                this.setSource(state.source.type, state.source.id, state.source.name);
            }

            // Wait for metadata then seek and play
            this.audio.addEventListener('loadedmetadata', () => {
                this.audio.currentTime = state.currentTime || 0;
                if (state.isPlaying) {
                    this.play();
                }
            }, { once: true });
            this.audio.load();
        } catch (e) {
            console.warn('Could not restore audio state:', e);
        }
    }
}

let audioPlayer;

document.addEventListener('DOMContentLoaded', () => {
    audioPlayer = new AudioPlayer();
    document.addEventListener('click', (e) => {
        const trackCard = e.target.closest('.track-card');
        if (trackCard) {
            const title = trackCard.querySelector('h3')?.textContent || '';
            const artist = trackCard.querySelector('p')?.textContent || '';
            const trackId = trackCard.dataset.trackId;
            document.querySelectorAll('.track-card').forEach(card => {
                card.classList.remove('playing');
            });
            trackCard.classList.add('playing');
            if (trackId) {
                fetch(`http://127.0.0.1:8000/tracks/${trackId}`)
                    .then(response => response.json())
                    .then(track => {
                        audioPlayer.playTrack({
                            url: track.track_file,
                            title: track.track_title,
                            artist: track.artist_info?.artist_name || artist,
                            trackId: trackId
                        });
                    })
                    .catch(error => {
                        console.error('Error fetching track details:', error);
                    });
            }
        }
    });
});
