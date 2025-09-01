class ChatConfig {
    constructor() {
        console.log('Initializing ChatConfig');
        this.config = {
            theme: 'oracle',
            secondaryColor: '#000000', // Oracle black
            wallpaper: null,
            lastUser: 'user1',
            transparency: 0.9, // Default transparency (0.9 = 90% opacity)
            maxTokens: 1000
        };
        this.loadConfig();
    }

    loadConfig() {
        try {
            const savedConfig = localStorage.getItem('chatConfig');
            if (savedConfig) {
                this.config = { ...this.config, ...JSON.parse(savedConfig) };
                this.applyConfig();
            }
            console.log('Config loaded:', this.config);
        } catch (error) {
            console.error('Error loading config:', error);
        }
    }

    saveConfig() {
        try {
            localStorage.setItem('chatConfig', JSON.stringify(this.config));
            console.log('Config saved:', this.config);
        } catch (error) {
            console.error('Error saving config:', error);
        }
    }

    setTheme(color, isOracle = false) {
        console.log('Setting theme:', color, 'isOracle:', isOracle);
        this.config.theme = color;
        if (isOracle) {
            this.config.secondaryColor = '#000000';
            document.documentElement.style.setProperty('--secondary-color', '#000000');
        }
        document.documentElement.style.setProperty('--primary-color', color);
        this.saveConfig();
        this.applyConfig();
    }

    setWallpaper(imageData) {
        console.log('Setting wallpaper');
        this.config.wallpaper = imageData;
        if (imageData) {
            document.body.style.backgroundImage = `url(${imageData})`;
            document.body.style.backgroundSize = 'cover';
            document.body.style.backgroundPosition = 'center';
        } else {
            document.body.style.backgroundImage = 'none';
        }
        this.saveConfig();
        this.applyConfig();
    }

    setLastUser(user) {
        console.log('Setting last user:', user);
        this.config.lastUser = user;
        this.saveConfig();
    }

    setTransparency(value) {
        console.log('Setting transparency:', value);
        this.config.transparency = value;
        const chatContainer = document.querySelector('.chat-container');
        if (chatContainer) {
            chatContainer.style.backgroundColor = `rgba(255, 255, 255, ${value})`;
        }
        this.saveConfig();
        this.applyConfig();
    }

    setMaxTokens(value) {
        this.config.maxTokens = value;
        this.saveConfig();
    }

    applyConfig() {
        console.log('Applying config');
        // Apply theme
        if (this.config.theme) {
            document.documentElement.style.setProperty('--primary-color', this.config.theme);
        }
        if (this.config.secondaryColor) {
            document.documentElement.style.setProperty('--secondary-color', this.config.secondaryColor);
        }

        // Apply wallpaper
        if (this.config.wallpaper) {
            document.body.style.backgroundImage = `url(${this.config.wallpaper})`;
            document.body.style.backgroundSize = 'cover';
            document.body.style.backgroundPosition = 'center';
        }

        // Apply last user
        if (this.config.lastUser) {
            const userSelect = document.getElementById('userSelect');
            if (userSelect) {
                userSelect.value = this.config.lastUser;
            }
        }

        // Apply transparency
        if (this.config.transparency) {
            const chatContainer = document.querySelector('.chat-container');
            if (chatContainer) {
                chatContainer.style.backgroundColor = `rgba(255, 255, 255, ${this.config.transparency})`;
            }
        }
    }
}

// Create global instance
const chatConfig = new ChatConfig(); 