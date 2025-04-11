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
    
    // Initialize simulator
    initEinkSimulator();
    
    // Load code
    loadCode();
});

function setupButtonListeners() {
    console.log('Setting up button listeners...');
    
    // Service button
    setupButtonListener('btnShowServices', function() {
        showContent('servicesCard');
    });
    
    // Display simulator button
    setupButtonListener('btnDisplaySimulator', function() {
        showContent('displaySimulatorCard');
    });
    
    // Code walkthrough button
    setupButtonListener('btnCodeWalkthrough', function() {
        showContent('codeWalkthroughCard');
    });
    
    // E-Ink simulator buttons
    setupButtonListener('btnUpdateDisplay', function() {
        updateEinkDisplay();
    });
    
    setupButtonListener('btnClearDisplay', function() {
        clearEinkDisplay();
    });
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
        
        S["Service\\n${service.name}\\nUUID: ${service.uuid.slice(0, 8)}..."]:::service`;
        
        // Add characteristics with simpler formatting
        service.characteristics.forEach((char, index) => {
            const charId = `C${index}`;
            const properties = char.properties.join(', ');
            
            mermaidCode += `
            ${charId}["Char: ${char.name}\\nUUID: ${char.uuid.slice(0, 8)}...\\nProperties: ${properties}"]:::characteristic
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
        classDef startup fill:#e6f7ff,stroke:#1890ff,stroke-width:2px
        classDef active fill:#f6ffed,stroke:#52c41a,stroke-width:2px
        classDef process fill:#fff7e6,stroke:#fa8c16,stroke-width:1px
        classDef event fill:#f9f0ff,stroke:#722ed1,stroke-width:1px
        
        init["Initialize Hardware"]:::startup
        scan["Scan for Advertisements"]:::active
        connect["Establish Connection"]:::active
        discover["Discover Services"]:::process
        subscribe["Subscribe to Notifications"]:::process
        receive["Receive Updates"]:::active
        display["Update E-Ink Display"]:::process
        disconnect["Handle Disconnection"]:::event
        
        init --> scan
        scan --> connect
        connect --> discover
        discover --> subscribe
        subscribe --> receive
        receive --> display
        display --> receive
        
        receive -.-> disconnect
        disconnect -.-> scan`;
        
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

function initEinkSimulator() {
    console.log('Initializing E-Ink display simulator...');
    
    // Initialize the E-Ink display content
    const einkContent = document.getElementById('einkContent');
    const einkDisplay = document.getElementById('einkDisplay');
    
    if (einkContent && einkDisplay) {
        // Ensure content is visible
        einkContent.style.display = 'flex';
        einkContent.style.justifyContent = 'center';
        einkContent.style.alignItems = 'center';
        einkContent.style.color = 'black';
        einkContent.style.fontSize = '12px';
        einkContent.style.textAlign = 'center';
        
        console.log('E-Ink display initialized with text:', einkContent.innerText);
    } else {
        console.error('E-Ink display elements not found during initialization');
    }
}

function updateEinkDisplay() {
    const displayText = document.getElementById('displayText');
    const einkContent = document.getElementById('einkContent');
    const einkDisplay = document.getElementById('einkDisplay');
    
    if (!displayText || !einkContent || !einkDisplay) {
        console.error('E-Ink simulator elements not found!');
        return;
    }
    
    const text = displayText.value.trim();
    if (text) {
        updateStatus('Updating display...');
        
        // Add refreshing animation
        einkDisplay.classList.add('refreshing');
        
        // Update after animation delay
        setTimeout(function() {
            // Make sure the text is visible by setting it directly
            einkContent.style.display = 'flex';
            einkContent.innerText = text;
            einkContent.style.color = 'black';
            einkContent.style.fontSize = '12px';
            einkContent.style.justifyContent = 'center';
            einkContent.style.alignItems = 'center';
            einkContent.style.textAlign = 'center';
            einkContent.style.zIndex = '10';
            
            // Double check the content is visible
            if (window.getComputedStyle(einkContent).display === 'none') {
                console.log('Forcing display style');
                einkContent.setAttribute('style', 'display: flex !important; color: black; font-size: 12px; justify-content: center !important; align-items: center !important; text-align: center; z-index: 10;');
            }
            
            updateStatus('Display updated');
            einkDisplay.classList.remove('refreshing');
            console.log('E-Ink display updated with text:', text);
        }, 1000);
    } else {
        console.log('No text to display');
    }
}

function clearEinkDisplay() {
    const einkContent = document.getElementById('einkContent');
    const einkDisplay = document.getElementById('einkDisplay');
    
    if (!einkContent || !einkDisplay) {
        console.error('E-Ink simulator elements not found!');
        return;
    }
    
    updateStatus('Clearing display...');
    
    // Add refreshing animation
    einkDisplay.classList.add('refreshing');
    
    // Clear after animation delay
    setTimeout(function() {
        einkContent.innerText = '';
        einkContent.style.display = 'flex';
        einkContent.style.justifyContent = 'center';
        einkContent.style.alignItems = 'center';
        einkContent.style.color = 'black';
        einkContent.style.fontSize = '12px';
        einkContent.style.textAlign = 'center';
        
        updateStatus('Display cleared');
        einkDisplay.classList.remove('refreshing');
        console.log('E-Ink display cleared');
    }, 1000);
}

function updateStatus(status) {
    const statusSpan = document.getElementById('deviceStatus');
    if (statusSpan) {
        statusSpan.innerText = status;
        console.log('Status updated:', status);
    } else {
        console.error('Status span not found!');
    }
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