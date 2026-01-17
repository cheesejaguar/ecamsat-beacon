/**
 * EcAMSat Beacon Decoder - Frontend Application
 */

// API base URL - adjust for production
const API_BASE = '';

// DOM Elements
const packetInput = document.getElementById('packet-input');
const charCount = document.getElementById('char-count');
const decodeBtn = document.getElementById('decode-btn');
const loadSampleBtn = document.getElementById('load-sample');
const errorMessage = document.getElementById('error-message');
const resultsSection = document.getElementById('results-section');

// Sample packets for demo
let samplePackets = [];
let currentSampleIndex = 0;

/**
 * Initialize the application
 */
async function init() {
    // Set up event listeners
    packetInput.addEventListener('input', handleInputChange);
    decodeBtn.addEventListener('click', decodePacket);
    loadSampleBtn.addEventListener('click', loadSample);

    // Allow Enter key to decode
    packetInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            decodePacket();
        }
    });

    // Fetch sample packets
    await fetchSamples();
}

/**
 * Handle input changes and update character count
 */
function handleInputChange() {
    const length = packetInput.value.trim().length;
    charCount.textContent = length;

    // Visual feedback for correct length
    if (length === 64) {
        charCount.style.color = '#10b981';
    } else if (length > 64) {
        charCount.style.color = '#ef4444';
    } else {
        charCount.style.color = '#3b82f6';
    }

    // Clear error when typing
    hideError();
}

/**
 * Fetch sample packets from the API
 */
async function fetchSamples() {
    try {
        const response = await fetch(`${API_BASE}/api/samples`);
        if (response.ok) {
            const data = await response.json();
            samplePackets = data.samples;
        }
    } catch (error) {
        console.error('Failed to fetch samples:', error);
        // Fallback samples
        samplePackets = [
            { packet: 'EcAMSat.org   1DEA21020033021EBA02A80200004400F90830A23661515F5B', description: 'Sample packet' },
            { packet: 'EcAMSat.org   D900220000C6010F5B00A2014F005100B3082ACC3C674A5F5B', description: 'Sample packet' },
        ];
    }
}

/**
 * Load a sample packet into the input
 */
function loadSample() {
    if (samplePackets.length === 0) return;

    const sample = samplePackets[currentSampleIndex];
    packetInput.value = sample.packet;
    currentSampleIndex = (currentSampleIndex + 1) % samplePackets.length;

    handleInputChange();

    // Auto-decode the sample
    decodePacket();
}

/**
 * Show error message
 */
function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove('hidden');
    resultsSection.classList.add('hidden');
}

/**
 * Hide error message
 */
function hideError() {
    errorMessage.classList.add('hidden');
}

/**
 * Set loading state on decode button
 */
function setLoading(loading) {
    if (loading) {
        decodeBtn.classList.add('loading');
        decodeBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <path d="M12 6v6l4 2"/>
            </svg>
            Decoding...
        `;
    } else {
        decodeBtn.classList.remove('loading');
        decodeBtn.innerHTML = `
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M13 10V3L4 14h7v7l9-11h-7z"/>
            </svg>
            Decode Packet
        `;
    }
}

/**
 * Decode the beacon packet
 */
async function decodePacket() {
    const packet = packetInput.value.trim();

    if (!packet) {
        showError('Please enter a beacon packet');
        return;
    }

    hideError();
    setLoading(true);

    try {
        const response = await fetch(`${API_BASE}/api/decode`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ packet }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Failed to decode packet');
        }

        displayResults(data);
    } catch (error) {
        showError(error.message);
    } finally {
        setLoading(false);
    }
}

/**
 * Format a number with appropriate precision
 */
function formatNumber(num, decimals = 2) {
    if (typeof num !== 'number') return num;
    return num.toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: decimals,
    });
}

/**
 * Display decoded results
 */
function displayResults(data) {
    // Show results section
    resultsSection.classList.remove('hidden');

    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });

    // Update basic fields
    document.getElementById('bus-time').textContent = formatNumber(data.bus_time_seconds, 0);
    document.getElementById('data-type').textContent = data.data_type;
    document.getElementById('data-type-name').textContent = data.type_specific_data.type_name;
    document.getElementById('well-number').textContent = data.well_number;
    document.getElementById('page-number').textContent = data.payload_page_number;

    // Solar panel data
    document.getElementById('solar-panel-num').textContent = data.solar_panel.panel_number;
    document.getElementById('solar-current').textContent = formatNumber(data.solar_panel.current_ma);
    document.getElementById('solar-temp').textContent = formatNumber(data.solar_panel.temperature_c);

    // Temperature
    document.getElementById('card-temp').textContent = formatNumber(data.median_card_temp_c);

    // Light sensors
    document.getElementById('taos-r').textContent = formatNumber(data.light_sensors.red_hz, 0);
    document.getElementById('taos-g').textContent = formatNumber(data.light_sensors.green_hz, 0);
    document.getElementById('taos-b').textContent = formatNumber(data.light_sensors.blue_hz, 0);

    // Raw packet
    document.getElementById('raw-packet').textContent = data.raw_packet;

    // Type-specific data
    displayTypeSpecificData(data.data_type, data.type_specific_data);
}

/**
 * Display type-specific telemetry data
 */
function displayTypeSpecificData(dataType, typeData) {
    const section = document.querySelector('.type-data-section');
    const grid = document.getElementById('type-data-grid');
    const title = document.getElementById('type-section-title');

    // Remove old type class and add new one
    section.className = 'panel-section type-data-section type-' + dataType;

    // Update title
    title.innerHTML = `
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
        </svg>
        ${typeData.type_name} Data
    `;

    // Build grid items based on data type
    let gridHTML = '';

    switch (dataType) {
        case 1:
            gridHTML = `
                <div class="panel-item">
                    <span class="panel-label">Power Port Status</span>
                    <span class="panel-value">${typeData.power_port_status}</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Payload Board Temp</span>
                    <span class="panel-value">${formatNumber(typeData.payload_board_temp_c)}</span>
                    <span class="panel-unit">&deg;C</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Battery Voltage</span>
                    <span class="panel-value">${formatNumber(typeData.battery_voltage_v)}</span>
                    <span class="panel-unit">V</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Payload Heater Current</span>
                    <span class="panel-value">${formatNumber(typeData.payload_heater_current_ma)}</span>
                    <span class="panel-unit">mA</span>
                </div>
            `;
            break;

        case 2:
            gridHTML = `
                <div class="panel-item">
                    <span class="panel-label">Startup Counter</span>
                    <span class="panel-value">${typeData.startup_counter}</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Radiation Counts</span>
                    <span class="panel-value">${typeData.radiation_counts_per_30s}</span>
                    <span class="panel-unit">per 30s</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Comm Voltage</span>
                    <span class="panel-value">${formatNumber(typeData.comm_voltage_v)}</span>
                    <span class="panel-unit">V</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Payload Current</span>
                    <span class="panel-value">${formatNumber(typeData.payload_current_ma)}</span>
                    <span class="panel-unit">mA</span>
                </div>
            `;
            break;

        case 3:
            gridHTML = `
                <div class="panel-item">
                    <span class="panel-label">Spacecraft ID</span>
                    <span class="panel-value">${typeData.spacecraft_ground_id}</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Comm Current</span>
                    <span class="panel-value">${formatNumber(typeData.comm_current_ma)}</span>
                    <span class="panel-unit">mA</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Sensor Voltage</span>
                    <span class="panel-value">${formatNumber(typeData.sensor_voltage_v)}</span>
                    <span class="panel-unit">V</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Bus Data Page</span>
                    <span class="panel-value">${typeData.bus_data_page}</span>
                </div>
            `;
            break;

        case 4:
            gridHTML = `
                <div class="panel-item">
                    <span class="panel-label">Experiment Phase</span>
                    <span class="panel-value">${typeData.experiment_phase}</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Comm Voltage</span>
                    <span class="panel-value">${formatNumber(typeData.comm_voltage_v)}</span>
                    <span class="panel-unit">V</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Bus Voltage</span>
                    <span class="panel-value">${formatNumber(typeData.bus_voltage_v)}</span>
                    <span class="panel-unit">V</span>
                </div>
                <div class="panel-item">
                    <span class="panel-label">Wrap Count</span>
                    <span class="panel-value">${typeData.register_file_wrap_count}</span>
                </div>
            `;
            break;
    }

    grid.innerHTML = gridHTML;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
