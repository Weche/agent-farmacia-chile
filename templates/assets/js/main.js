/**
 * Pharmacy Finder - Main Application Logic
 * Modern implementation with Netflix/YouTube-inspired UI
 * Created: August 30, 2025
 */

export class PharmacyFinder {
    constructor() {
        this.map = null;
        this.markers = [];
        this.pharmacies = [];
        this.userLocation = null;
        this.userMarker = null;
        this.timeUpdateInterval = null;
        this.currentFilter = 'all';
        
        // Bind methods to preserve context
        this.performSearch = this.performSearch.bind(this);
        this.getUserLocation = this.getUserLocation.bind(this);
        this.clearResults = this.clearResults.bind(this);
        this.handleQuickAction = this.handleQuickAction.bind(this);
        this.handleFilterChip = this.handleFilterChip.bind(this);
        
        this.init();
    }
    
    init() {
        console.log('🗺️ Initializing Pharmacy Finder...');
        this.initMap();
        this.loadInitialData();
        this.setupEventListeners();
        this.setupAnimations();
    }
    
    initMap() {
        // Initialize map centered on Chile
        this.map = L.map('map').setView([-33.4489, -70.6693], 10);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        // Custom pharmacy icons
        this.pharmacyIcon = L.icon({
            iconUrl: 'data:image/svg+xml;base64,' + btoa(`
                <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="16" cy="16" r="15" fill="#667eea" stroke="white" stroke-width="2"/>
                    <rect x="13" y="8" width="6" height="16" fill="white"/>
                    <rect x="8" y="13" width="16" height="6" fill="white"/>
                </svg>
            `),
            iconSize: [32, 32],
            iconAnchor: [16, 16],
            popupAnchor: [0, -16]
        });

        this.openPharmacyIcon = L.icon({
            iconUrl: 'data:image/svg+xml;base64,' + btoa(`
                <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="16" cy="16" r="15" fill="#4CAF50" stroke="white" stroke-width="2"/>
                    <rect x="13" y="8" width="6" height="16" fill="white"/>
                    <rect x="8" y="13" width="16" height="6" fill="white"/>
                </svg>
            `),
            iconSize: [32, 32],
            iconAnchor: [16, 16],
            popupAnchor: [0, -16]
        });

        this.onDutyIcon = L.icon({
            iconUrl: 'data:image/svg+xml;base64,' + btoa(`
                <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="16" cy="16" r="15" fill="#FF9800" stroke="white" stroke-width="2"/>
                    <rect x="13" y="8" width="6" height="16" fill="white"/>
                    <rect x="8" y="13" width="16" height="6" fill="white"/>
                </svg>
            `),
            iconSize: [32, 32],
            iconAnchor: [16, 16],
            popupAnchor: [0, -16]
        });
    }
    
    setupEventListeners() {
        // Search functionality
        const searchBtn = document.getElementById('search-btn');
        const searchInput = document.getElementById('search-input');
        const locationBtn = document.getElementById('location-btn');
        const clearBtn = document.getElementById('clear-btn');
        
        if (searchBtn) searchBtn.addEventListener('click', this.performSearch);
        if (locationBtn) locationBtn.addEventListener('click', this.getUserLocation);
        if (clearBtn) clearBtn.addEventListener('click', this.clearResults);
        
        // Enter key in search input
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch();
                }
            });
        }
        
        // Quick action buttons
        const actionNearMe = document.getElementById('actionNearMe');
        const actionOpenNow = document.getElementById('actionOpenNow');
        const actionMedications = document.getElementById('actionMedications');
        
        if (actionNearMe) actionNearMe.addEventListener('click', () => this.handleQuickAction('nearMe'));
        if (actionOpenNow) actionOpenNow.addEventListener('click', () => this.handleQuickAction('openNow'));
        if (actionMedications) actionMedications.addEventListener('click', () => this.handleQuickAction('medications'));
        
        // Filter chips
        const filterChips = document.querySelectorAll('.chip[data-filter]');
        filterChips.forEach(chip => {
            chip.addEventListener('click', () => this.handleFilterChip(chip.dataset.filter));
        });
        
        // Hero chat input
        const chatInputHero = document.getElementById('chatInputHero');
        const chatSendHero = document.getElementById('chatSendHero');
        
        if (chatInputHero) {
            chatInputHero.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.sendHeroMessage();
                }
            });
        }
        
        if (chatSendHero) {
            chatSendHero.addEventListener('click', this.sendHeroMessage.bind(this));
        }
    }
    
    setupAnimations() {
        // Intersection Observer for fade-in animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            });
        }, observerOptions);
        
        // Observe fade-in elements
        document.querySelectorAll('.fade-in').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(el);
        });
    }
    
    async loadInitialData() {
        try {
            this.showLoading('Cargando datos iniciales...');
            
            // Load statistics
            const statsResponse = await fetch('/api/stats');
            const stats = await statsResponse.json();
            this.updateStats(stats);

            // Load communes for autocomplete
            await this.loadCommunes();

            // Load some initial pharmacies (Santiago area)
            await this.searchPharmacies('santiago', false);
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Error al cargar datos iniciales');
        } finally {
            this.hideLoading();
        }
    }
    
    async loadCommunes() {
        try {
            const response = await fetch('/api/communes');
            const data = await response.json();
            
            const datalist = document.getElementById('communes-list');
            if (datalist) {
                datalist.innerHTML = '';
                data.communes.forEach(commune => {
                    const option = document.createElement('option');
                    option.value = commune;
                    datalist.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading communes:', error);
        }
    }
    
    async performSearch() {
        const searchInput = document.getElementById('search-input');
        const filterSelect = document.getElementById('filter-select');
        
        if (!searchInput || !filterSelect) return;
        
        const query = searchInput.value.trim();
        const filter = filterSelect.value;

        if (!query) {
            this.showError('Por favor ingresa una comuna para buscar');
            searchInput.focus();
            return;
        }

        const onlyOpen = filter === 'open';
        const onlyOpenNow = filter === 'open-now';
        await this.searchPharmacies(query, onlyOpen, onlyOpenNow);
    }
    
    async searchPharmacies(query, onlyOpen, onlyOpenNow = false) {
        try {
            this.showLoading('🔍 Buscando farmacias...');

            let response;
            if (onlyOpenNow) {
                const params = new URLSearchParams({ comuna: query });
                response = await fetch(`/api/open-now?${params}`);
            } else {
                const params = new URLSearchParams({
                    comuna: query,
                    abierto: onlyOpen
                });
                response = await fetch(`/api/search?${params}`);
            }

            const data = await response.json();

            if (response.ok) {
                this.displayResults(data.items || []);
                this.updateResultsCount(data.items?.length || 0, query);
            } else {
                this.showError('Error al buscar farmacias: ' + (data.detail || 'Error desconocido'));
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Error de conexión. Intenta nuevamente.');
        } finally {
            this.hideLoading();
        }
    }
    
    async getUserLocation() {
        if (!navigator.geolocation) {
            this.showError('Tu navegador no soporta geolocalización');
            this.useDefaultLocation();
            return;
        }

        this.showLoading('📍 Obteniendo tu ubicación...');

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;
                this.userLocation = { lat: latitude, lng: longitude };

                // Add user marker
                if (this.userMarker) {
                    this.map.removeLayer(this.userMarker);
                }

                this.userMarker = L.marker([latitude, longitude])
                    .addTo(this.map)
                    .bindPopup('📍 Tu ubicación')
                    .openPopup();

                // Center map on user location
                this.map.setView([latitude, longitude], 13);

                // Search for nearby pharmacies
                await this.searchNearbyPharmacies(latitude, longitude);
                this.hideLoading();
            },
            (error) => {
                console.error('Geolocation error:', error);
                
                let errorMessage = 'Error al obtener tu ubicación. ';
                switch(error.code) {
                    case 1:
                        errorMessage += 'Permiso denegado. Por favor permite el acceso a la ubicación.';
                        break;
                    case 2:
                        errorMessage += 'Ubicación no disponible.';
                        break;
                    case 3:
                        errorMessage += 'Tiempo agotado.';
                        break;
                    default:
                        errorMessage += 'Error desconocido.';
                }
                
                this.showError(errorMessage);
                this.useDefaultLocation();
            },
            {
                enableHighAccuracy: false,
                timeout: 15000,
                maximumAge: 600000
            }
        );
    }
    
    useDefaultLocation() {
        const defaultLat = -33.4489;
        const defaultLng = -70.6693;
        
        this.userLocation = { lat: defaultLat, lng: defaultLng };

        if (this.userMarker) {
            this.map.removeLayer(this.userMarker);
        }

        this.userMarker = L.marker([defaultLat, defaultLng])
            .addTo(this.map)
            .bindPopup('📍 Ubicación aproximada (Santiago)')
            .openPopup();

        this.map.setView([defaultLat, defaultLng], 11);
        this.searchNearbyPharmacies(defaultLat, defaultLng);
        this.hideLoading();
    }
    
    async searchNearbyPharmacies(lat, lng) {
        try {
            const filterSelect = document.getElementById('filter-select');
            const filter = filterSelect?.value || 'all';
            
            const onlyOpen = filter === 'open';
            const onlyOpenNow = filter === 'open-now';

            const params = new URLSearchParams({
                lat: lat,
                lng: lng,
                radius: 5,
                abierto: onlyOpen,
                abierto_ahora: onlyOpenNow
            });

            const response = await fetch(`/api/nearby?${params}`);
            const data = await response.json();

            if (response.ok) {
                this.displayResults(data.items || []);
                this.updateResultsCount(data.items?.length || 0, 'cerca de tu ubicación');
            } else {
                this.showError('Error al buscar farmacias cercanas');
            }
        } catch (error) {
            console.error('Nearby search error:', error);
            this.showError('Error al buscar farmacias cercanas');
        }
    }
    
    displayResults(pharmacies) {
        this.clearMapMarkers();
        this.pharmacies = pharmacies;

        if (pharmacies.length === 0) {
            this.showNoResults();
            return;
        }

        // Add markers to map
        const bounds = [];
        pharmacies.forEach((pharmacy, index) => {
            if (pharmacy.lat && pharmacy.lng && pharmacy.lat !== 0 && pharmacy.lng !== 0) {
                const isOpen = pharmacy.abierto_ahora !== undefined ? pharmacy.abierto_ahora : false;
                const isOnDuty = pharmacy.es_turno || false;
                
                let icon = this.pharmacyIcon;
                if (isOpen) icon = this.openPharmacyIcon;
                else if (isOnDuty) icon = this.onDutyIcon;

                const marker = L.marker([pharmacy.lat, pharmacy.lng], { icon: icon })
                    .addTo(this.map)
                    .bindPopup(this.createPopupContent(pharmacy));

                // Add click handler to center on pharmacy
                marker.on('click', () => {
                    this.highlightPharmacyCard(index);
                });

                this.markers.push(marker);
                bounds.push([pharmacy.lat, pharmacy.lng]);
            }
        });

        // Fit map to show all markers
        if (bounds.length > 0) {
            this.map.fitBounds(bounds, { padding: [20, 20] });
        }

        // Display results grid
        this.displayResultsGrid(pharmacies);
    }
    
    createPopupContent(pharmacy) {
        const isCurrentlyOpen = pharmacy.abierto_ahora !== undefined ? pharmacy.abierto_ahora : pharmacy.es_turno;
        const statusClass = isCurrentlyOpen ? 'status-open' : 'status-closed';
        const statusText = isCurrentlyOpen ? '🟢 Abierto Ahora' : '🔴 Cerrado';

        return `
            <div style="font-family: var(--font-primary); max-width: 280px; color: var(--text-primary);">
                <h4 style="margin: 0 0 8px 0; color: var(--text-primary); font-size: 16px;">${pharmacy.nombre}</h4>
                <p style="margin: 0 0 6px 0; color: var(--text-secondary); font-size: 14px;">📍 ${pharmacy.direccion}</p>
                <p style="margin: 0 0 6px 0; color: var(--text-secondary); font-size: 14px;">🏙️ ${pharmacy.comuna}</p>
                <p style="margin: 0 0 6px 0; color: var(--text-secondary); font-size: 14px;">📞 ${pharmacy.telefono || 'No disponible'}</p>
                <p style="margin: 0 0 6px 0; color: var(--text-secondary); font-size: 14px;">🕐 ${pharmacy.hora_apertura} - ${pharmacy.hora_cierre}</p>
                <div style="margin-top: 8px;">
                    <span style="
                        display: inline-block;
                        padding: 4px 8px;
                        border-radius: 12px;
                        font-size: 12px;
                        font-weight: 600;
                        background: ${isCurrentlyOpen ? '#4CAF50' : '#F44336'};
                        color: white;
                    ">${statusText}</span>
                </div>
            </div>
        `;
    }
    
    displayResultsGrid(pharmacies) {
        const container = document.getElementById('results-container');
        if (!container) return;

        if (pharmacies.length === 0) {
            this.showNoResults();
            return;
        }

        const gridHTML = `
            <div class="pharmacy-grid">
                ${pharmacies.map((pharmacy, index) => this.createPharmacyCard(pharmacy, index)).join('')}
            </div>
        `;

        container.innerHTML = gridHTML;
        
        // Add click handlers to cards
        this.setupCardClickHandlers();
    }
    
    createPharmacyCard(pharmacy, index) {
        const isCurrentlyOpen = pharmacy.abierto_ahora !== undefined ? pharmacy.abierto_ahora : pharmacy.es_turno;
        const statusClass = isCurrentlyOpen ? 'open' : 'closed';
        const statusText = isCurrentlyOpen ? 'Abierto' : 'Cerrado';
        
        const isOnDuty = pharmacy.es_turno || false;
        const isFeatured = isCurrentlyOpen || isOnDuty;

        return `
            <div class="pharmacy-card ${isFeatured ? 'featured' : ''}" data-pharmacy-index="${index}">
                <div class="card-image">
                    <div class="pharmacy-icon">🏥</div>
                    <div class="status-badge ${statusClass}">${statusText}</div>
                </div>
                <div class="card-content">
                    <h3 class="pharmacy-name">${pharmacy.nombre}</h3>
                    <p class="pharmacy-address">📍 ${pharmacy.direccion}, ${pharmacy.comuna}</p>
                    <div class="pharmacy-details">
                        <div class="pharmacy-detail">
                            <span class="pharmacy-detail-icon">📞</span>
                            <span>${pharmacy.telefono || 'No disponible'}</span>
                        </div>
                        <div class="pharmacy-detail">
                            <span class="pharmacy-detail-icon">🕐</span>
                            <span>${pharmacy.hora_apertura} - ${pharmacy.hora_cierre}</span>
                        </div>
                    </div>
                    <div class="card-actions">
                        <button class="btn-card btn-card-primary" onclick="app.centerOnPharmacy(${index})">
                            Ver en mapa
                        </button>
                        <button class="btn-card btn-card-secondary" onclick="app.showPharmacyDetails(${index})">
                            Más info
                        </button>
                    </div>
                </div>
                <div class="card-overlay">
                    <button class="chat-about-this" onclick="app.chatAboutPharmacy(${index})">
                        💬 Preguntar sobre esta farmacia
                    </button>
                </div>
            </div>
        `;
    }
    
    setupCardClickHandlers() {
        const cards = document.querySelectorAll('.pharmacy-card');
        cards.forEach((card, index) => {
            card.addEventListener('click', (e) => {
                // Don't trigger if clicking on buttons
                if (e.target.tagName === 'BUTTON') return;
                
                this.centerOnPharmacy(index);
                this.highlightPharmacyCard(index);
            });
        });
    }
    
    centerOnPharmacy(index) {
        const pharmacy = this.pharmacies[index];
        if (pharmacy && pharmacy.lat && pharmacy.lng) {
            this.map.setView([pharmacy.lat, pharmacy.lng], 15);

            // Find and open the corresponding marker popup
            if (this.markers[index]) {
                this.markers[index].openPopup();
            }
        }
    }
    
    highlightPharmacyCard(index) {
        // Remove previous highlights
        document.querySelectorAll('.pharmacy-card').forEach(card => {
            card.classList.remove('highlighted');
        });
        
        // Highlight selected card
        const card = document.querySelector(`[data-pharmacy-index="${index}"]`);
        if (card) {
            card.classList.add('highlighted');
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }
    
    showPharmacyDetails(index) {
        const pharmacy = this.pharmacies[index];
        if (!pharmacy) return;
        
        // Create detailed modal or panel (to be implemented)
        alert(`Detalles de ${pharmacy.nombre}:\n\nDirección: ${pharmacy.direccion}\nComuna: ${pharmacy.comuna}\nTeléfono: ${pharmacy.telefono}\nHorario: ${pharmacy.hora_apertura} - ${pharmacy.hora_cierre}`);
    }
    
    chatAboutPharmacy(index) {
        const pharmacy = this.pharmacies[index];
        if (!pharmacy) return;
        
        // Send message to chat about this pharmacy
        if (window.chatManager) {
            const message = `Cuéntame más sobre la farmacia ${pharmacy.nombre} en ${pharmacy.direccion}, ${pharmacy.comuna}`;
            window.chatManager.sendMessage(message);
            window.chatManager.openChat();
        }
    }
    
    handleQuickAction(action) {
        switch (action) {
            case 'nearMe':
                this.getUserLocation();
                break;
            case 'openNow':
                const filterSelect = document.getElementById('filter-select');
                if (filterSelect) {
                    filterSelect.value = 'open-now';
                    this.performSearch();
                }
                break;
            case 'medications':
                if (window.chatManager) {
                    window.chatManager.sendMessage('¿Qué medicamentos puedes ayudarme a encontrar?');
                    window.chatManager.openChat();
                }
                break;
        }
    }
    
    handleFilterChip(filter) {
        // Update active chip
        document.querySelectorAll('.chip').forEach(chip => {
            chip.classList.remove('active');
        });
        
        const activeChip = document.querySelector(`[data-filter="${filter}"]`);
        if (activeChip) {
            activeChip.classList.add('active');
        }
        
        this.currentFilter = filter;
        
        // Apply filter to current results
        this.applyFilter(filter);
    }
    
    applyFilter(filter) {
        const cards = document.querySelectorAll('.pharmacy-card');
        
        cards.forEach((card, index) => {
            const pharmacy = this.pharmacies[index];
            let show = true;
            
            switch (filter) {
                case 'open':
                    show = pharmacy.es_turno;
                    break;
                case 'open-now':
                    show = pharmacy.abierto_ahora;
                    break;
                case 'nearby':
                    // This would require distance calculation
                    show = this.userLocation ? true : false;
                    break;
                case 'all':
                default:
                    show = true;
                    break;
            }
            
            card.style.display = show ? 'flex' : 'none';
        });
        
        // Update results count
        const visibleCards = document.querySelectorAll('.pharmacy-card[style="display: flex;"], .pharmacy-card:not([style*="display: none"])').length;
        this.updateResultsCount(visibleCards, `filtrado por ${filter}`);
    }
    
    sendHeroMessage() {
        const input = document.getElementById('chatInputHero');
        if (!input || !input.value.trim()) return;
        
        const message = input.value.trim();
        input.value = '';
        
        if (window.chatManager) {
            window.chatManager.sendMessage(message);
            window.chatManager.openChat();
        }
    }
    
    clearMapMarkers() {
        this.markers.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.markers = [];
    }
    
    clearResults() {
        const searchInput = document.getElementById('search-input');
        const filterSelect = document.getElementById('filter-select');
        
        if (searchInput) searchInput.value = '';
        if (filterSelect) filterSelect.value = 'all';
        
        this.clearMapMarkers();
        this.pharmacies = [];
        
        const container = document.getElementById('results-container');
        if (container) {
            container.innerHTML = `
                <div class="pharmacy-grid-empty">
                    <div class="empty-icon">🔍</div>
                    <div class="empty-title">Busca tu farmacia ideal</div>
                    <div class="empty-description">
                        Usa el buscador o nuestro asistente inteligente para encontrar farmacias cerca de ti.
                    </div>
                    <button class="btn btn-primary" onclick="document.getElementById('search-input').focus()">
                        Comenzar búsqueda
                    </button>
                </div>
            `;
        }
        
        this.updateResultsCount(0, 'búsqueda limpiada');
        this.map.setView([-33.4489, -70.6693], 10);
    }
    
    updateStats(stats) {
        const elements = {
            'total-pharmacies': stats.total || 0,
            'open-pharmacies': stats.turno || 0,
            'communes-count': stats.communes || 0
        };
        
        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                this.animateNumber(element, parseInt(element.textContent) || 0, value);
            }
        });
        
        // Update current time
        if (stats.current_time) {
            const timeElement = document.getElementById('current-time');
            if (timeElement) {
                timeElement.textContent = stats.current_time;
            }
        } else {
            this.updateCurrentTime();
        }
        
        // Start time updates
        if (!this.timeUpdateInterval) {
            this.timeUpdateInterval = setInterval(() => {
                this.updateCurrentTime();
            }, 1000);
        }
    }
    
    animateNumber(element, start, end, duration = 1000) {
        const startTime = performance.now();
        const difference = end - start;
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.round(start + (difference * easeOut));
            
            element.textContent = current.toLocaleString();
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }
    
    updateCurrentTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString('es-CL', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        const timeElement = document.getElementById('current-time');
        if (timeElement) {
            timeElement.textContent = timeString;
        }
    }
    
    updateResultsCount(count, context = '') {
        const element = document.getElementById('results-count');
        if (element) {
            if (count === 0) {
                element.textContent = `No se encontraron farmacias${context ? ' para ' + context : ''}`;
            } else {
                element.textContent = `${count} farmacia${count !== 1 ? 's' : ''} encontrada${count !== 1 ? 's' : ''}${context ? ' ' + context : ''}`;
            }
        }
    }
    
    showLoading(message = 'Cargando...') {
        const container = document.getElementById('results-container');
        if (container) {
            container.innerHTML = `
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <span>${message}</span>
                </div>
            `;
        }
    }
    
    hideLoading() {
        // Loading will be replaced by results or error message
    }
    
    showError(message) {
        const container = document.getElementById('results-container');
        if (container) {
            container.innerHTML = `
                <div class="error">
                    ❌ ${message}
                </div>
            `;
        }
    }
    
    showNoResults() {
        const container = document.getElementById('results-container');
        if (container) {
            container.innerHTML = `
                <div class="pharmacy-grid-empty">
                    <div class="empty-icon">😔</div>
                    <div class="empty-title">No se encontraron farmacias</div>
                    <div class="empty-description">
                        Intenta buscar en otra comuna o usar diferentes filtros.
                    </div>
                    <button class="btn btn-primary" onclick="app.clearResults()">
                        Nueva búsqueda
                    </button>
                </div>
            `;
        }
    }
    
    // Public API for external access
    getPharmacies() {
        return this.pharmacies;
    }
    
    getUserLocation() {
        return this.userLocation;
    }
    
    getMap() {
        return this.map;
    }
    
    // **UPDATE MAP WITH USER LOCATION AND SEARCH NEARBY PHARMACIES**
    async updateMapWithUserLocation(latitude, longitude) {
        console.log('🗺️ Updating map with user location:', latitude, longitude);
        
        // Store user location
        this.userLocation = { lat: latitude, lng: longitude };
        
        // Remove existing user marker if any
        if (this.userMarker) {
            this.map.removeLayer(this.userMarker);
        }
        
        // Create custom user location icon (blue with white center)
        const userLocationIcon = L.icon({
            iconUrl: 'data:image/svg+xml;base64,' + btoa(`
                <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="16" cy="16" r="15" fill="#4285f4" stroke="white" stroke-width="3"/>
                    <circle cx="16" cy="16" r="8" fill="white"/>
                    <circle cx="16" cy="16" r="4" fill="#4285f4"/>
                </svg>
            `),
            iconSize: [32, 32],
            iconAnchor: [16, 16],
            popupAnchor: [0, -16]
        });
        
        // Add new user marker
        this.userMarker = L.marker([latitude, longitude], {
            icon: userLocationIcon
        })
        .addTo(this.map)
        .bindPopup('📍 Tu ubicación actual')
        .openPopup();
        
        // Center map on user location with appropriate zoom
        this.map.setView([latitude, longitude], 14);
        
        // Search for nearby pharmacies and update map
        try {
            await this.searchNearbyPharmacies(latitude, longitude);
            console.log('✅ Map updated with user location and nearby pharmacies');
        } catch (error) {
            console.error('❌ Error searching nearby pharmacies:', error);
        }
    }
    
    // **SHOW PHARMACIES ON MAP**
    showPharmaciesOnMap(pharmacies, userLocation = null) {
        console.log('🗺️ Showing pharmacies on map:', pharmacies.length, 'pharmacies');
        console.log('📍 User location provided:', userLocation);
        
        // Clear existing pharmacy markers
        this.clearPharmacyMarkers();
        
        // Store pharmacies for other methods to use
        this.pharmacies = pharmacies;
        
        const bounds = [];
        
        // Add user location marker and to bounds if provided
        if (userLocation && userLocation.latitud && userLocation.longitud) {
            const userLat = parseFloat(userLocation.latitud);
            const userLng = parseFloat(userLocation.longitud);
            
            if (!isNaN(userLat) && !isNaN(userLng)) {
                console.log('📍 Adding user location to map:', userLat, userLng);
                
                // Add user location to bounds
                bounds.push([userLat, userLng]);
                
                // Update map with user location (adds blue marker)
                this.updateMapWithUserLocation(userLat, userLng);
            }
        }
        
        // Add pharmacy markers
        pharmacies.forEach((pharmacy, index) => {
            // Get coordinates - handle different possible structures
            let lat, lng;
            
            if (pharmacy.coordenadas) {
                lat = pharmacy.coordenadas.latitud || pharmacy.coordenadas.lat;
                lng = pharmacy.coordenadas.longitud || pharmacy.coordenadas.lng;
            } else if (pharmacy.latitud && pharmacy.longitud) {
                lat = pharmacy.latitud;
                lng = pharmacy.longitud;
            } else if (pharmacy.lat && pharmacy.lng) {
                lat = pharmacy.lat;
                lng = pharmacy.lng;
            }
            
            if (lat && lng) {
                const parsedLat = parseFloat(lat);
                const parsedLng = parseFloat(lng);
                
                if (!isNaN(parsedLat) && !isNaN(parsedLng)) {
                    // Add pharmacy to bounds
                    bounds.push([parsedLat, parsedLng]);
                    
                    // Determine if pharmacy is open
                    const isOpen = pharmacy.abierta || pharmacy.turno;
                    
                    // Create pharmacy marker with appropriate icon
                    const pharmacyIcon = L.icon({
                        iconUrl: 'data:image/svg+xml;base64,' + btoa(`
                            <svg width="32" height="32" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg">
                                <circle cx="16" cy="16" r="15" fill="${isOpen ? '#28a745' : '#dc3545'}" stroke="white" stroke-width="2"/>
                                <rect x="13" y="8" width="6" height="16" fill="white"/>
                                <rect x="8" y="13" width="16" height="6" fill="white"/>
                            </svg>
                        `),
                        iconSize: [32, 32],
                        iconAnchor: [16, 32],
                        popupAnchor: [0, -32]
                    });
                    
                    // Create popup content
                    const popupContent = `
                        <div style="min-width: 200px;">
                            <h4 style="margin: 0 0 8px 0; color: #2c3e50;">${pharmacy.nombre || 'Farmacia'}</h4>
                            <p style="margin: 4px 0; font-size: 12px; color: ${isOpen ? '#28a745' : '#dc3545'};">
                                ${isOpen ? '🟢 Abierta' : '🔴 Cerrada'}
                            </p>
                            <p style="margin: 4px 0; font-size: 12px;">📍 ${pharmacy.direccion || 'Dirección no disponible'}</p>
                            ${pharmacy.telefono ? `<p style="margin: 4px 0; font-size: 12px;">📞 ${pharmacy.telefono}</p>` : ''}
                            <button onclick="app.focusPharmacyOnMap(${index})" style="margin-top: 8px; padding: 4px 8px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer;">
                                Ver detalles
                            </button>
                        </div>
                    `;
                    
                    // Add marker to map
                    const marker = L.marker([parsedLat, parsedLng], { 
                        icon: pharmacyIcon,
                        pharmacy: pharmacy  // Store pharmacy reference
                    })
                        .addTo(this.map)
                        .bindPopup(popupContent);
                    
                    // Store marker reference
                    this.markers.push(marker);
                }
            }
        });
        
        // Fit map to show all markers if we have any bounds
        if (bounds.length > 0) {
            console.log('🗺️ Fitting map to bounds with', bounds.length, 'points');
            this.map.fitBounds(bounds, { 
                padding: [20, 20],
                maxZoom: 15  // Don't zoom in too close
            });
        }
        
        console.log('✅ Added', this.markers.length, 'pharmacy markers to map');
    }
    
    // **CLEAR PHARMACY MARKERS**
    clearPharmacyMarkers() {
        this.markers.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.markers = [];
    }

    focusPharmacyOnMap(pharmacyIndex) {
        if (!this.pharmacies || this.pharmacies.length === 0) {
            console.error('No pharmacy data available');
            return;
        }

        const pharmacy = this.pharmacies[pharmacyIndex];
        if (!pharmacy) {
            console.error('Invalid pharmacy index:', pharmacyIndex);
            return;
        }

        if (!pharmacy.lat || !pharmacy.lng) {
            console.error('Invalid pharmacy data for map focus');
            return;
        }

        const lat = parseFloat(pharmacy.lat);
        const lng = parseFloat(pharmacy.lng);

        if (isNaN(lat) || isNaN(lng)) {
            console.error('Invalid coordinates for pharmacy:', pharmacy);
            return;
        }

        // Center map on pharmacy location
        this.map.setView([lat, lng], 16);

        // Find and highlight the pharmacy marker
        this.markers.forEach(marker => {
            const markerPharmacy = marker.options.pharmacy;
            if (markerPharmacy && (markerPharmacy.id === pharmacy.id || 
                (markerPharmacy.lat === pharmacy.lat && markerPharmacy.lng === pharmacy.lng))) {
                // Open popup for this pharmacy
                marker.openPopup();
                
                // Add highlighting effect
                const markerElement = marker.getElement();
                if (markerElement) {
                    markerElement.style.filter = 'brightness(1.5) drop-shadow(0 0 10px #007bff)';
                    setTimeout(() => {
                        markerElement.style.filter = '';
                    }, 3000);
                }
            }
        });
    }

    askAboutPharmacy(pharmacyIndex) {
        if (!this.pharmacies || this.pharmacies.length === 0) {
            console.error('No pharmacy data available');
            return;
        }

        const pharmacy = this.pharmacies[pharmacyIndex];
        if (!pharmacy) {
            console.error('Invalid pharmacy index:', pharmacyIndex);
            return;
        }

        const question = `Cuéntame más sobre la farmacia ${pharmacy.nombre || 'esta farmacia'}`;
        
        // Get chat interface elements
        const chatInput = document.getElementById('userInput');
        const sendButton = document.getElementById('sendButton');

        if (chatInput && sendButton) {
            // Set the question in the input
            chatInput.value = question;
            
            // Trigger the send action
            sendButton.click();
            
            // Focus on chat input for user interaction
            chatInput.focus();
            
            // Scroll to chat section
            const chatSection = document.getElementById('chat-section');
            if (chatSection) {
                chatSection.scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            console.error('Chat interface elements not found');
            // Fallback: try to call sendMessage directly if available
            if (window.sendMessage) {
                window.sendMessage(question);
            }
        }
    }
}

// Make PharmacyFinder available globally for backward compatibility
window.PharmacyFinder = PharmacyFinder;
