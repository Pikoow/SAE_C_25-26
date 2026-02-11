class AudioPlayer {
    constructor() {
        this.audio = new Audio();
        this.currentTrack = null;
        this.isPlaying = false;
        this.volume = 0.7;
        this.audio.volume = this.volume;
        
        this.createPlayerUI();
        this.setupEventListeners();
    }
    
    createPlayerUI() {
        this.playerContainer = document.createElement('div');
        this.playerContainer.id = 'audio-player-container';
        this.playerContainer.innerHTML = `
            <div class="player-left">
                <div class="track-title" id="current-track-title">Aucune musique</div>
                <div class="artist-name" id="current-artist-name">Sélectionnez une piste</div>
            </div>
            
            <div class="player-center">
                <button id="stop-btn" class="stop-btn" disabled>
                    <svg viewBox="0 0 24 24" fill="currentColor">
                        <rect x="6" y="6" width="12" height="12"/>
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
            </div>
            
            <div class="player-right">
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
                z-index: 1000;
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
                gap: 6px;
                justify-self: end;
                font-size: 13px;
                color: rgba(255, 255, 255, 0.7);
                font-variant-numeric: tabular-nums;
            }

            .time-separator {
                color: rgba(255, 255, 255, 0.4);
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
            this.stop();
        });
        
        this.audio.addEventListener('play', () => {
            this.isPlaying = true;
            this.updatePlayPauseButton();
        });
        
        this.audio.addEventListener('pause', () => {
            this.isPlaying = false;
            this.updatePlayPauseButton();
        });
    }
    
    convertTrackUrl(dbUrl) {
        if (!dbUrl) return '';
        let path = dbUrl.startsWith('music/') ? dbUrl.substring(6) : dbUrl;
        return `https://files.freemusicarchive.org/storage-freemusicarchive-org/music/${path}`;
    }
    
    playTrack(trackInfo) {
        const { url, title, artist } = trackInfo;
        
        if (!url) {
            console.error('No track URL provided');
            return;
        }
        
        const fullUrl = this.convertTrackUrl(url);
        
        this.currentTrack = {
            url: fullUrl,
            title: title || 'Titre inconnu',
            artist: artist || 'Artiste inconnu'
        };
        
        this.audio.src = fullUrl;
        this.trackTitleEl.textContent = this.currentTrack.title;
        this.artistNameEl.textContent = this.currentTrack.artist;
        
        this.play();
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
                            artist: track.artist_info?.artist_name || artist
                        });
                    })
                    .catch(error => {
                        console.error('Error fetching track details:', error);
                    });
            }
        }
    });
});
