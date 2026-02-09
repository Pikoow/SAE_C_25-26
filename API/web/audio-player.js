class AudioPlayer {
    constructor() {
        this.audio = new Audio();
        this.currentTrack = null;
        this.isPlaying = false;
        this.volume = 0.5;
        this.audio.volume = this.volume;
        
        this.createPlayerUI();
        this.setupEventListeners();
    }
    
    createPlayerUI() {
        // Create player container
        this.playerContainer = document.createElement('div');
        this.playerContainer.id = 'audio-player-container';
        this.playerContainer.innerHTML = `
            <div class="player-info">
                <div class="track-title" id="current-track-title">Aucune musique sélectionnée</div>
                <div class="artist-name" id="current-artist-name"></div>
            </div>
            <div class="player-controls">
                <button id="play-pause-btn" class="control-btn" disabled>
                    <span class="play-icon">▶</span>
                    <span class="pause-icon" style="display: none;">⏸</span>
                </button>
                <button id="stop-btn" class="control-btn" disabled>⏹</button>
                <div class="volume-control">
                    <button id="mute-btn" class="control-btn">🔊</button>
                    <input type="range" id="volume-slider" min="0" max="1" step="0.1" value="0.5">
                </div>
                <div class="progress-container">
                    <input type="range" id="progress-bar" min="0" max="100" value="0" class="progress-bar" disabled>
                    <div class="time-display">
                        <span id="current-time">0:00</span> / <span id="total-time">0:00</span>
                    </div>
                </div>
            </div>
        `;
        
        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            #audio-player-container {
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 20px;
                box-shadow: 0 -2px 10px rgba(0,0,0,0.3);
                z-index: 1000;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-family: Arial, sans-serif;
            }
            
            .player-info {
                flex: 1;
                min-width: 200px;
            }
            
            .track-title {
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 5px;
            }
            
            .artist-name {
                font-size: 14px;
                opacity: 0.9;
            }
            
            .player-controls {
                flex: 2;
                display: flex;
                align-items: center;
                gap: 15px;
                max-width: 600px;
            }
            
            .control-btn {
                background: rgba(255,255,255,0.2);
                border: none;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                color: white;
                font-size: 16px;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.3s;
            }
            
            .control-btn:hover:not(:disabled) {
                background: rgba(255,255,255,0.3);
            }
            
            .control-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }
            
            .volume-control {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            #volume-slider {
                width: 80px;
                height: 5px;
                -webkit-appearance: none;
                background: rgba(255,255,255,0.3);
                border-radius: 5px;
                outline: none;
            }
            
            #volume-slider::-webkit-slider-thumb {
                -webkit-appearance: none;
                width: 15px;
                height: 15px;
                border-radius: 50%;
                background: white;
                cursor: pointer;
            }
            
            .progress-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                gap: 5px;
            }
            
            .progress-bar {
                width: 100%;
                height: 5px;
                -webkit-appearance: none;
                background: rgba(255,255,255,0.3);
                border-radius: 5px;
                outline: none;
            }
            
            .progress-bar::-webkit-slider-thumb {
                -webkit-appearance: none;
                width: 15px;
                height: 15px;
                border-radius: 50%;
                background: white;
                cursor: pointer;
            }
            
            .progress-bar:disabled::-webkit-slider-thumb {
                background: rgba(255,255,255,0.5);
                cursor: not-allowed;
            }
            
            .time-display {
                font-size: 12px;
                opacity: 0.8;
                display: flex;
                justify-content: space-between;
            }
            
            .track-card {
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            .track-card:hover {
                transform: translateY(-2px);
            }
            
            .track-card.playing {
                background: rgba(102, 126, 234, 0.1);
                border-left: 3px solid #667eea;
            }
        `;
        
        document.head.appendChild(style);
        document.body.appendChild(this.playerContainer);
        
        // Store DOM elements
        this.playPauseBtn = document.getElementById('play-pause-btn');
        this.stopBtn = document.getElementById('stop-btn');
        this.volumeSlider = document.getElementById('volume-slider');
        this.muteBtn = document.getElementById('mute-btn');
        this.progressBar = document.getElementById('progress-bar');
        this.currentTimeEl = document.getElementById('current-time');
        this.totalTimeEl = document.getElementById('total-time');
        this.trackTitleEl = document.getElementById('current-track-title');
        this.artistNameEl = document.getElementById('current-artist-name');
    }
    
    setupEventListeners() {
        // Play/Pause button
        this.playPauseBtn.addEventListener('click', () => {
            if (this.isPlaying) {
                this.pause();
            } else {
                this.play();
            }
        });
        
        // Stop button
        this.stopBtn.addEventListener('click', () => {
            this.stop();
        });
        
        // Volume slider
        this.volumeSlider.addEventListener('input', (e) => {
            this.setVolume(parseFloat(e.target.value));
        });
        
        // Mute button
        this.muteBtn.addEventListener('click', () => {
            this.toggleMute();
        });
        
        // Progress bar
        this.progressBar.addEventListener('input', (e) => {
            const time = (e.target.value / 100) * this.audio.duration;
            this.audio.currentTime = time;
        });
        
        // Audio events
        this.audio.addEventListener('timeupdate', () => {
            this.updateProgress();
        });
        
        this.audio.addEventListener('loadedmetadata', () => {
            this.updateTimeDisplay();
            this.progressBar.disabled = false;
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
        
        // Convert the database URL to the full URL
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
        this.progressBar.value = 0;
        this.currentTimeEl.textContent = '0:00';
        this.isPlaying = false;
        this.updatePlayPauseButton();
    }
    
    setVolume(volume) {
        this.volume = volume;
        this.audio.volume = volume;
        
        // Update mute button icon
        if (volume === 0) {
            this.muteBtn.textContent = '🔇';
        } else if (volume < 0.5) {
            this.muteBtn.textContent = '🔈';
        } else {
            this.muteBtn.textContent = '🔊';
        }
    }
    
    toggleMute() {
        if (this.audio.volume > 0) {
            this.audio.volume = 0;
            this.volumeSlider.value = 0;
            this.muteBtn.textContent = '🔇';
        } else {
            this.audio.volume = this.volume || 0.5;
            this.volumeSlider.value = this.volume || 0.5;
            this.muteBtn.textContent = '🔊';
        }
    }
    
    updateProgress() {
        if (this.audio.duration) {
            const progress = (this.audio.currentTime / this.audio.duration) * 100;
            this.progressBar.value = progress;
            this.updateTimeDisplay();
        }
    }
    
    updateTimeDisplay() {
        const formatTime = (seconds) => {
            const mins = Math.floor(seconds / 60);
            const secs = Math.floor(seconds % 60);
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        };
        
        this.currentTimeEl.textContent = formatTime(this.audio.currentTime || 0);
        
        if (this.audio.duration && !isNaN(this.audio.duration)) {
            this.totalTimeEl.textContent = formatTime(this.audio.duration);
        }
    }
    
    updatePlayPauseButton() {
        const playIcon = this.playPauseBtn.querySelector('.play-icon');
        const pauseIcon = this.playPauseBtn.querySelector('.pause-icon');
        
        if (this.isPlaying) {
            playIcon.style.display = 'none';
            pauseIcon.style.display = 'inline';
        } else {
            playIcon.style.display = 'inline';
            pauseIcon.style.display = 'none';
        }
    }
}

// Initialize player globally
let audioPlayer;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    audioPlayer = new AudioPlayer();
    
    // Add click handlers to track cards (modify existing ones)
    document.addEventListener('click', (e) => {
        const trackCard = e.target.closest('.track-card');
        if (trackCard) {
            // Extract track info from card
            const title = trackCard.querySelector('h3')?.textContent || '';
            const artist = trackCard.querySelector('p')?.textContent || '';
            const trackId = trackCard.dataset.trackId;
            
            // Remove playing class from all cards
            document.querySelectorAll('.track-card').forEach(card => {
                card.classList.remove('playing');
            });
            
            // Add playing class to current card
            trackCard.classList.add('playing');
            
            // If we have track ID, fetch the full track info
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