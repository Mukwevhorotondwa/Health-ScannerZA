const API_BASE_URL = 'http://127.0.0.1:5000/api/product/'; 

// --- DOM Elements ---
const inputSection = document.getElementById('input-section');
const resultSection = document.getElementById('result-section');
const errorSection = document.getElementById('error-section');

const barcodeInput = document.getElementById('barcode-input');
const checkButton = document.getElementById('check-button');
const cameraButton = document.getElementById('camera-button');
const cameraIcon = document.getElementById('camera-icon');
const scannerContainer = document.getElementById('scanner-container');
const manualInputArea = document.getElementById('manual-input-area'); // 🔑 NEW
const scanAnotherButton = document.getElementById('scan-another-button');
const tryAgainButton = document.getElementById('try-again-button');
const errorMessage = document.getElementById('error-message');

const productNameEl = document.getElementById('product-name');
const productBrandEl = document.getElementById('product-brand');
const productCategoryEl = document.getElementById('product-category');
const scoreTextEl = document.getElementById('score-text');
const scoreBadgeEl = document.getElementById('score-badge');
const keyIndicatorsEl = document.getElementById('key-indicators');
const nutritionBreakdownEl = document.getElementById('nutrition-breakdown');
const additivesListEl = document.getElementById('additives-list');

let isCameraRunning = false; 

// --- Helper Functions ---

function getScoreClass(score) {
    if (score === 'A') return 'score-A';
    if (score === 'B') return 'score-B';
    if (score === 'C') return 'score-C';
    if (score === 'D') return 'score-D';
    if (score === 'E') return 'score-E';
    return 'score-NA';
}

function createIndicatorBadges(nutrition) {
    const indicators = [];

    // 1. High/Low Salt 
    if (nutrition.salt > 1.2) {
        indicators.push({ text: 'High Salt', icon: '🚨', type: 'negative' });
    } else if (nutrition.salt < 0.3) {
        indicators.push({ text: 'Low Salt', icon: '✅', type: 'positive' });
    }

    // 2. High Sugar 
    if (nutrition.sugar > 20) {
        indicators.push({ text: 'High Sugar', icon: '🛑', type: 'negative' });
    } else if (nutrition.sugar < 5) {
        indicators.push({ text: 'Low Sugar', icon: '✅', type: 'positive' });
    }
    
    // 3. Saturated Fat 
    if (nutrition.saturated_fat > 5) { 
        indicators.push({ text: 'High Sat. Fat', icon: '⚠️', type: 'negative' });
    }

    // 4. Fiber/Protein 
    if (nutrition.fiber > 6) { 
        indicators.push({ text: 'Good Source of Fiber', icon: '⭐', type: 'positive' });
    }
    if (nutrition.protein > 10) { 
        indicators.push({ text: 'Good Protein Source', icon: '💪', type: 'positive' });
    }
    
    return indicators;
}

function renderResults(data) {
    stopScanner(); 
    
    // 1. Set Header Info & Score
    productNameEl.textContent = data.name || 'Unknown Product';
    productBrandEl.textContent = data.brand || 'Unknown Brand';
    productCategoryEl.textContent = data.category || 'General';

    const scoreLetter = data.health_score || 'N/A';
    scoreTextEl.textContent = scoreLetter;
    
    scoreBadgeEl.className = 'score-badge'; 
    scoreBadgeEl.classList.add(getScoreClass(scoreLetter));

    // 2. Render Key Indicators
    keyIndicatorsEl.innerHTML = '';
    
    const nutrition = data.nutrition_per_100g;
    const indicators = createIndicatorBadges(nutrition);

    if (indicators.length > 0) {
        indicators.forEach(indicator => {
            const badge = document.createElement('div');
            badge.className = `indicator-badge indicator-${indicator.type}`;
            badge.innerHTML = `<span class="indicator-icon">${indicator.icon}</span>${indicator.text}`;
            keyIndicatorsEl.appendChild(badge);
        });
    } else {
        keyIndicatorsEl.innerHTML = '<p style="text-align: center; color: var(--color-text-light);">No prominent positive or negative traits found.</p>';
    }

    // 3. Render Nutrition Breakdown
    nutritionBreakdownEl.innerHTML = '';
    const nutritionDisplayOrder = [
        { key: 'calories', label: 'Calories', unit: 'kcal' },
        { key: 'sugar', label: 'Sugar', unit: 'g' },
        { key: 'saturated_fat', label: 'Sat. Fat', unit: 'g' },
        { key: 'salt', label: 'Salt', unit: 'g' },
        { key: 'protein', label: 'Protein', unit: 'g' },
        { key: 'fiber', label: 'Fiber', unit: 'g' },
        { key: 'fat', label: 'Total Fat', unit: 'g' },
    ];

    nutritionDisplayOrder.forEach(item => {
        const value = (nutrition[item.key] !== undefined && nutrition[item.key] !== null) 
                      ? nutrition[item.key].toFixed(1) 
                      : 'N/A';
        
        const itemEl = document.createElement('div');
        itemEl.className = 'data-item';
        itemEl.innerHTML = `<strong>${value} ${item.unit}</strong> ${item.label}`;
        nutritionBreakdownEl.appendChild(itemEl);
    });

    // 4. Render Additives
    additivesListEl.innerHTML = '';
    if (data.additives && data.additives.length > 0) {
        data.additives.forEach(additive => {
            const li = document.createElement('li');
            li.textContent = additive;
            additivesListEl.appendChild(li);
        });
    } else {
        additivesListEl.innerHTML = '<li>No significant additives found.</li>';
    }

    // 5. Update View
    inputSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    resultSection.classList.remove('hidden');
}

function displayError(message) {
    stopScanner();
    errorMessage.textContent = message;
    inputSection.classList.add('hidden');
    resultSection.classList.add('hidden');
    errorSection.classList.remove('hidden');
}

function resetView() {
    stopScanner();
    barcodeInput.value = '';
    resultSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    inputSection.classList.remove('hidden');
}


// --- QuaggaJS Scanner Logic ---

function startScanner() {
    Quagga.init({
        inputStream : {
            name : "Live",
            type : "LiveStream",
            target: document.querySelector('#interactive'),
            constraints: {
                facingMode: "environment" 
            }
        },
        decoder : {
            readers : ["ean_reader"] 
        },
        locator: {
            patchSize: "medium",
            halfSample: true
        }
    }, function(err) {
        if (err) {
            console.error(err);
            alert("Error starting camera. Ensure you are on HTTPS or localhost: " + err.message);
            stopScanner();
            return;
        }
        Quagga.start();
        isCameraRunning = true;
        
        // Update UI
        cameraIcon.textContent = '🛑';
        cameraButton.textContent = 'Stop Scanning';
        scannerContainer.classList.remove('hidden');
        manualInputArea.classList.add('hidden'); // 🔑 HIDE MANUAL INPUT
        checkButton.disabled = true; 
        barcodeInput.disabled = true;
    });

    Quagga.onDetected(function(result) {
        const code = result.codeResult.code;
        console.log("Barcode detected:", code);
        
        stopScanner();
        barcodeInput.value = code;
        handleScan(code);
    });
}

function stopScanner() {
    if (isCameraRunning) {
        Quagga.stop();
        isCameraRunning = false;
        
        // Reset UI
        cameraIcon.textContent = '📷';
        cameraButton.textContent = 'Scan with Camera';
        scannerContainer.classList.add('hidden');
        manualInputArea.classList.remove('hidden'); // 🔑 SHOW MANUAL INPUT
        checkButton.disabled = false;
        barcodeInput.disabled = false;
    }
}

function toggleScanner() {
    if (isCameraRunning) {
        stopScanner();
    } else {
        startScanner();
    }
}


// --- Main Action Handler ---

async function handleScan(barcodeToScan = null) {
    const barcode = barcodeToScan || barcodeInput.value.trim();
    if (!barcode) {
        displayError("Please enter or scan a barcode to check.");
        return;
    }
    
    checkButton.textContent = 'Checking...';
    checkButton.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}${barcode}`);
        const data = await response.json();

        if (response.ok) {
            renderResults(data);
        } else if (response.status === 404) {
            displayError(`Product with barcode ${barcode} not found.`);
        } else {
            displayError(`An API error occurred: ${data.error || 'Server Error'}`);
        }

    } catch (error) {
        console.error('Fetch error:', error);
        displayError("Could not connect to the Health Scanner API. Please check the server connection.");
    } finally {
        checkButton.textContent = 'CHECK BARCODE';
        checkButton.disabled = false;
    }
}


// --- Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    cameraButton.addEventListener('click', toggleScanner);
    checkButton.addEventListener('click', () => handleScan()); 
    
    barcodeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleScan();
        }
    });

    scanAnotherButton.addEventListener('click', resetView);
    tryAgainButton.addEventListener('click', resetView);
    
    resetView(); 
});