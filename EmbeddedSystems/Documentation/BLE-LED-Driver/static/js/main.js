// Initialize Mermaid for diagrams
document.addEventListener('DOMContentLoaded', function() {
    console.clear();
    console.log('DOM loaded, initializing application...');
    
    // Initialize Mermaid diagrams
    if (typeof mermaid !== 'undefined') {
        console.log('Initializing Mermaid...');
        mermaid.initialize({ 
            startOnLoad: true, 
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {
                useMaxWidth: false,
                htmlLabels: true
            }
        });
    } else {
        console.error('Mermaid library not found!');
    }
    
    // Initialize button listeners
    setupButtonListeners();
    
    // Load content
    loadServicesDiagram();
    loadFlowDiagram();
    loadHardwareInfo();
    
    // Initialize LED simulator
    initLEDSimulator();
    
    // Load code
    loadCode();
});

function setupButtonListeners() {
    console.log('Setting up button listeners...');
    
    // Service button
    setupButtonListener('btnShowServices', function() {
        showContent('servicesCard');
    });
    
    // Simulator button
    setupButtonListener('btnLEDSimulator', function() {
        showContent('ledSimulatorCard');
    });
    
    // Code walkthrough button
    setupButtonListener('btnCodeWalkthrough', function() {
        showContent('codeWalkthroughCard');
    });
    
    // Color preset buttons
    document.querySelectorAll('.color-preset').forEach(function(preset) {
        preset.addEventListener('click', function() {
            const rgb = preset.getAttribute('data-rgb').split(',');
            document.getElementById('redSlider').value = rgb[0];
            document.getElementById('greenSlider').value = rgb[1];
            document.getElementById('blueSlider').value = rgb[2];
            updateRGBDisplay();
        });
    });
    
    // RGB sliders
    setupSliderListener('redSlider');
    setupSliderListener('greenSlider');
    setupSliderListener('blueSlider');
}

function setupButtonListener(buttonId, callback) {
    const button = document.getElementById(buttonId);
    if (button) {
        button.addEventListener('click', function(event) {
            console.log(`Button clicked: ${buttonId}`);
            callback(event);
        });
        console.log(`Listener set up for button: ${buttonId}`);
    } else {
        console.error(`Button not found: ${buttonId}`);
    }
}

function setupSliderListener(sliderId) {
    const slider = document.getElementById(sliderId);
    if (slider) {
        slider.addEventListener('input', function() {
            updateRGBDisplay();
        });
        console.log(`Listener set up for slider: ${sliderId}`);
    } else {
        console.error(`Slider not found: ${sliderId}`);
    }
}

function showContent(cardId) {
    console.log(`Showing content: ${cardId}`);
    
    // Get all content cards
    const contentCards = document.querySelectorAll('.card[id$="Card"]');
    
    // First hide all content cards except the flow diagram
    contentCards.forEach(function(card) {
        if (card.id !== 'flowDiagramCard') {
            if (card.id === cardId) {
                // This is the card we want to toggle
                if (card.classList.contains('d-none')) {
                    card.classList.remove('d-none');
                    console.log(`Displayed card: ${cardId}`);
                    
                    // Scroll to it
                    setTimeout(function() {
                        card.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }, 100);
                } else {
                    card.classList.add('d-none');
                    console.log(`Hidden card: ${cardId}`);
                }
            } else {
                // Hide other cards
                card.classList.add('d-none');
            }
        }
    });
}

function loadServicesDiagram() {
    console.log('Loading services diagram...');
    
    fetch('/api/services')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Services data loaded successfully');
            renderServicesDiagram(data);
        })
        .catch(error => {
            console.error('Error loading services data:', error);
        });
}

function renderServicesDiagram(data) {
    const servicesDiv = document.getElementById('servicesDiagram');
    if (!servicesDiv) {
        console.error('Services diagram container not found!');
        return;
    }
    
    try {
        const service = data.service;
        
        // Simplified mermaid code for better compatibility
        let mermaidCode = `graph TD
        classDef service fill:#e6f7ff,stroke:#1890ff,stroke-width:2px
        classDef characteristic fill:#f6ffed,stroke:#52c41a,stroke-width:1px
        
        S["Service\\n${service.name}\\nUUID: ${service.uuid}"]:::service`;
        
        // Add characteristics with simpler formatting
        service.characteristics.forEach((char, index) => {
            const charId = `C${index}`;
            const properties = char.properties.join(', ');
            
            mermaidCode += `
            ${charId}["Char: ${char.name}\\nUUID: ${char.uuid}\\nProperties: ${properties}"]:::characteristic
            S --> ${charId}`;
        });
        
        servicesDiv.innerHTML = `<div class="mermaid">${mermaidCode}</div>`;
        
        if (typeof mermaid !== 'undefined') {
            try {
                mermaid.render('servicesMermaidGraph', mermaidCode)
                    .then(result => {
                        servicesDiv.innerHTML = result.svg;
                        console.log('Services diagram rendered successfully');
                    })
                    .catch(error => {
                        console.error('Mermaid rendering error:', error);
                        servicesDiv.innerHTML = `<div class="alert alert-danger">Error rendering diagram: ${error.message}</div>`;
                    });
            } catch (e) {
                console.error('Mermaid initialization error:', e);
                servicesDiv.innerHTML = `<div class="alert alert-danger">Error rendering diagram: ${e.message}</div>`;
            }
        } else {
            console.error('Mermaid library not loaded');
            servicesDiv.innerHTML = `<div class="alert alert-warning">Mermaid library not loaded. Cannot render diagram.</div>`;
        }
    } catch (e) {
        console.error('Error rendering services diagram:', e);
        servicesDiv.innerHTML = `<div class="alert alert-danger">Error rendering diagram: ${e.message}</div>`;
    }
}

function loadFlowDiagram() {
    console.log('Loading flow diagram...');
    
    fetch('/api/flow')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Flow data loaded successfully');
            renderFlowDiagram(data);
        })
        .catch(error => {
            console.error('Error loading flow data:', error);
        });
}

function renderFlowDiagram(data) {
    const flowDiv = document.getElementById('flowDiagram');
    if (!flowDiv) {
        console.error('Flow diagram container not found!');
        return;
    }
    
    try {
        // Simplified state flow diagram
        let mermaidCode = `graph TD
        classDef init fill:#e6f7ff,stroke:#1890ff,stroke-width:2px
        classDef active fill:#f6ffed,stroke:#52c41a,stroke-width:2px
        classDef process fill:#fff7e6,stroke:#fa8c16,stroke-width:1px
        classDef event fill:#f9f0ff,stroke:#722ed1,stroke-width:1px
        
        init["Initialize"]:::init
        advertising["Advertising"]:::active
        connected["Connected"]:::active
        receiving["Receiving Commands"]:::process
        updating["Updating LEDs"]:::process
        disconnected["Disconnected"]:::event
        
        init --> advertising
        advertising --> connected
        connected --> receiving
        receiving --> updating
        updating --> receiving
        receiving -.-> disconnected
        disconnected -.-> advertising`;
        
        flowDiv.innerHTML = `<div class="mermaid">${mermaidCode}</div>`;
        
        if (typeof mermaid !== 'undefined') {
            try {
                mermaid.render('flowMermaidGraph', mermaidCode)
                    .then(result => {
                        flowDiv.innerHTML = result.svg;
                        console.log('Flow diagram rendered successfully');
                    })
                    .catch(error => {
                        console.error('Mermaid rendering error:', error);
                        flowDiv.innerHTML = `<div class="alert alert-danger">Error rendering diagram: ${error.message}</div>`;
                    });
            } catch (e) {
                console.error('Mermaid initialization error:', e);
                flowDiv.innerHTML = `<div class="alert alert-danger">Error rendering diagram: ${e.message}</div>`;
            }
        } else {
            console.error('Mermaid library not loaded');
            flowDiv.innerHTML = `<div class="alert alert-warning">Mermaid library not loaded. Cannot render diagram.</div>`;
        }
    } catch (e) {
        console.error('Error rendering flow diagram:', e);
        flowDiv.innerHTML = `<div class="alert alert-danger">Error rendering diagram: ${e.message}</div>`;
    }
}

function loadHardwareInfo() {
    console.log('Loading hardware information...');
    
    fetch('/api/hardware')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Hardware data loaded successfully');
            renderHardwareInfo(data);
        })
        .catch(error => {
            console.error('Error loading hardware data:', error);
        });
}

function renderHardwareInfo(data) {
    const hardwareDiv = document.getElementById('hardwareInfo');
    if (!hardwareDiv) {
        console.error('Hardware info container not found!');
        return;
    }
    
    try {
        let html = `<h4>Board: ${data.board}</h4>`;
        
        html += '<h5>LED Pins:</h5><ul>';
        data.leds.forEach(led => {
            html += `<li><strong>${led.color}:</strong> ${led.pin} (PWM: ${led.pwm ? 'Yes' : 'No'})</li>`;
        });
        html += '</ul>';
        
        html += `<h5>Status LED:</h5>`;
        html += `<p><strong>${data.status_led.name}:</strong> ${data.status_led.pin} - ${data.status_led.function}</p>`;
        
        hardwareDiv.innerHTML = html;
        console.log('Hardware info rendered successfully');
    } catch (e) {
        console.error('Error rendering hardware info:', e);
        hardwareDiv.innerHTML = `<div class="alert alert-danger">Error rendering hardware info: ${e.message}</div>`;
    }
}

function initLEDSimulator() {
    console.log('Initializing LED simulator...');
    updateRGBDisplay();
}

function updateRGBDisplay() {
    const redSlider = document.getElementById('redSlider');
    const greenSlider = document.getElementById('greenSlider');
    const blueSlider = document.getElementById('blueSlider');
    const ledDisplay = document.getElementById('ledDisplay');
    
    if (!redSlider || !greenSlider || !blueSlider || !ledDisplay) {
        console.error('LED simulator elements not found!');
        return;
    }
    
    const red = redSlider.value;
    const green = greenSlider.value;
    const blue = blueSlider.value;
    
    // Update value displays
    document.getElementById('redValue').textContent = red;
    document.getElementById('greenValue').textContent = green;
    document.getElementById('blueValue').textContent = blue;
    
    // Convert to hex
    const hexColor = rgbToHex(red, green, blue);
    document.getElementById('hexValue').textContent = hexColor;
    
    // Update LED color
    ledDisplay.style.backgroundColor = `rgb(${red}, ${green}, ${blue})`;
    
    // Add flash animation
    ledDisplay.classList.add('updating');
    setTimeout(() => {
        ledDisplay.classList.remove('updating');
    }, 500);
    
    console.log(`LED updated: RGB(${red}, ${green}, ${blue})`);
}

function rgbToHex(r, g, b) {
    return '#' + [r, g, b].map(x => {
        const hex = parseInt(x).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    }).join('');
}

function loadCode() {
    console.log('Loading code...');
    
    fetch('/api/code')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Code data loaded successfully');
            
            if (data.status === 'success') {
                const codeDisplay = document.getElementById('codeDisplay');
                if (codeDisplay) {
                    codeDisplay.textContent = data.code;
                    
                    // Check if highlight.js is available
                    if (typeof hljs !== 'undefined') {
                        try {
                            hljs.highlightAll();
                            console.log('Code highlighted successfully');
                        } catch (e) {
                            console.error('Highlight.js error:', e);
                        }
                    } else {
                        console.warn('Highlight.js not found, code will not be highlighted');
                    }
                } else {
                    console.error('Code display element not found!');
                }
            } else {
                console.error('Code load error:', data.message);
            }
        })
        .catch(error => {
            console.error('Error loading code:', error);
        });
} 