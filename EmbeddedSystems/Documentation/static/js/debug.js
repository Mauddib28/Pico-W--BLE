/**
 * Debug utility for the E-Ink Display documentation
 * This script adds a debug console to the page to help diagnose issues
 */

// Create debug console
document.addEventListener('DOMContentLoaded', function() {
    createDebugConsole();
    addEventListeners();
});

function createDebugConsole() {
    // Create console container
    const consoleContainer = document.createElement('div');
    consoleContainer.id = 'debug-console';
    consoleContainer.style.cssText = `
        position: fixed;
        bottom: 0;
        right: 0;
        width: 400px;
        height: 300px;
        background-color: rgba(0, 0, 0, 0.8);
        color: #0f0;
        font-family: monospace;
        font-size: 12px;
        padding: 10px;
        overflow-y: auto;
        z-index: 9999;
        display: none;
        border-top-left-radius: 5px;
    `;
    
    // Create toggle button
    const toggleButton = document.createElement('button');
    toggleButton.textContent = 'Debug';
    toggleButton.style.cssText = `
        position: fixed;
        bottom: 0;
        right: 0;
        background-color: #f00;
        color: white;
        border: none;
        padding: 5px 10px;
        z-index: 10000;
        cursor: pointer;
        font-family: sans-serif;
        font-size: 12px;
    `;
    
    // Create clear button
    const clearButton = document.createElement('button');
    clearButton.textContent = 'Clear';
    clearButton.style.cssText = `
        position: absolute;
        top: 10px;
        right: 10px;
        background-color: #333;
        color: white;
        border: none;
        padding: 2px 5px;
        cursor: pointer;
        font-size: 10px;
    `;
    
    // Create log content
    const logContent = document.createElement('div');
    logContent.id = 'debug-log';
    
    // Add elements to page
    consoleContainer.appendChild(clearButton);
    consoleContainer.appendChild(logContent);
    document.body.appendChild(toggleButton);
    document.body.appendChild(consoleContainer);
    
    // Add event listeners
    toggleButton.addEventListener('click', function() {
        if (consoleContainer.style.display === 'none') {
            consoleContainer.style.display = 'block';
        } else {
            consoleContainer.style.display = 'none';
        }
    });
    
    clearButton.addEventListener('click', function() {
        logContent.innerHTML = '';
    });
    
    // Override console methods
    const originalLog = console.log;
    const originalError = console.error;
    const originalWarn = console.warn;
    
    console.log = function() {
        originalLog.apply(console, arguments);
        logToDebugConsole('LOG', arguments);
    };
    
    console.error = function() {
        originalError.apply(console, arguments);
        logToDebugConsole('ERROR', arguments, '#ff6666');
    };
    
    console.warn = function() {
        originalWarn.apply(console, arguments);
        logToDebugConsole('WARN', arguments, '#ffcc00');
    };
    
    // Log initialization
    console.log('Debug console initialized');
}

function logToDebugConsole(type, args, color = null) {
    const logContent = document.getElementById('debug-log');
    if (!logContent) return;
    
    const entry = document.createElement('div');
    
    // Convert arguments to string
    let message = Array.from(args).map(arg => {
        if (typeof arg === 'object') {
            try {
                return JSON.stringify(arg);
            } catch (e) {
                return arg.toString();
            }
        }
        return arg;
    }).join(' ');
    
    entry.innerHTML = `<span style="color: #aaa;">[${new Date().toLocaleTimeString()}]</span> <strong style="color: ${color || '#fff'}">${type}:</strong> ${message}`;
    logContent.appendChild(entry);
    
    // Auto-scroll to bottom
    logContent.scrollTop = logContent.scrollHeight;
}

function addEventListeners() {
    // Monitor all button clicks
    document.addEventListener('click', function(e) {
        if (e.target.tagName === 'BUTTON') {
            console.log(`Button clicked: ${e.target.id || e.target.textContent}`);
        }
    });
    
    // Monitor DOM changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'attributes' && 
                mutation.attributeName === 'class' && 
                mutation.target.classList && 
                (mutation.target.classList.contains('d-none') || mutation.target.classList.contains('card'))) {
                
                const isVisible = !mutation.target.classList.contains('d-none');
                console.log(`Element ${mutation.target.id} visibility changed: ${isVisible ? 'visible' : 'hidden'}`);
            }
        });
    });
    
    observer.observe(document.body, { 
        attributes: true, 
        attributeFilter: ['class'],
        subtree: true
    });
}

// Helper to inspect element properties
window.inspectElement = function(selector) {
    const element = document.querySelector(selector);
    if (!element) {
        console.error(`Element not found: ${selector}`);
        return;
    }
    
    console.log(`Inspecting element: ${selector}`);
    console.log(`- Tag: ${element.tagName}`);
    console.log(`- ID: ${element.id}`);
    console.log(`- Classes: ${Array.from(element.classList)}`);
    console.log(`- Display: ${getComputedStyle(element).display}`);
    console.log(`- Visibility: ${getComputedStyle(element).visibility}`);
    console.log(`- Position: ${getComputedStyle(element).position}`);
    console.log(`- Dimensions: ${element.offsetWidth}x${element.offsetHeight}`);
    
    return element;
}; 