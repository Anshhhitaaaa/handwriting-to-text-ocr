document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const uploadSection = document.getElementById('upload-section');
    const previewSection = document.getElementById('preview-section');
    const resultSection = document.getElementById('result-section');
    const imagePreview = document.getElementById('image-preview');
    const cleanedPreview = document.getElementById('cleaned-preview');
    const extractBtn = document.getElementById('extract-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const copyBtn = document.getElementById('copy-btn');
    const downloadBtn = document.getElementById('download-btn');
    const tryAgainBtn = document.getElementById('try-again-btn');
    const extractedTextarea = document.getElementById('extracted-textarea');
    const wordCountVal = document.getElementById('word-count');
    const charCountVal = document.getElementById('char-count');
    const confidenceVal = document.getElementById('confidence');
    const loadingOverlay = document.getElementById('loading');
    const darkModeBtn = document.getElementById('dark-mode-btn');
    const langSelect = document.getElementById('lang-select');
    const historyList = document.getElementById('history-list');
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    const steps = [
        document.getElementById('step-1'),
        document.getElementById('step-2'),
        document.getElementById('step-3'),
        document.getElementById('step-4')
    ];

    let currentFile = null;
    // On Vercel, use relative path for API
    const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' 
        ? 'http://localhost:5000' 
        : '';

    // Theme Logic
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    darkModeBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });

    function updateThemeIcon(theme) {
        const icon = darkModeBtn.querySelector('i');
        icon.className = theme === 'light' ? 'fas fa-moon' : 'fas fa-sun';
    }

    // History Logic
    let extractions = JSON.parse(localStorage.getItem('extractions')) || [];
    renderHistory();

    function saveToHistory(text, confidence) {
        const entry = {
            text: text.substring(0, 50) + (text.length > 50 ? '...' : ''),
            fullText: text,
            confidence: confidence,
            date: new Date().toLocaleString()
        };
        extractions.unshift(entry);
        extractions = extractions.slice(0, 5); // Keep last 5
        localStorage.setItem('extractions', JSON.stringify(extractions));
        renderHistory();
    }

    function renderHistory() {
        if (extractions.length === 0) {
            historyList.innerHTML = '<p class="hint">No recent extractions yet.</p>';
            return;
        }
        historyList.innerHTML = extractions.map((entry, i) => `
            <div class="history-item" onclick="loadFromHistory(${i})">
                <div class="history-info">
                    <span class="history-text">${entry.text}</span>
                    <span class="history-date">${entry.date} | ${entry.confidence}%</span>
                </div>
                <i class="fas fa-chevron-right" style="color: var(--accent-color)"></i>
            </div>
        `).join('');
    }

    window.loadFromHistory = (index) => {
        const entry = extractions[index];
        extractedTextarea.value = entry.fullText;
        confidenceVal.textContent = `${entry.confidence}%`;
        updateStats();
        uploadSection.classList.add('hidden');
        previewSection.classList.add('hidden');
        resultSection.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    clearHistoryBtn.addEventListener('click', () => {
        extractions = [];
        localStorage.removeItem('extractions');
        renderHistory();
    });

    // Drag and Drop Logic
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('active');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('active');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('active');
        const files = e.dataTransfer.files;
        if (files.length) handleFile(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
    });

    function handleFile(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file (JPG or PNG).');
            return;
        }
        currentFile = file;
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            uploadSection.classList.add('hidden');
            previewSection.classList.remove('hidden');
            window.scrollTo({ top: 0, behavior: 'smooth' });
        };
        reader.readAsDataURL(file);
    }

    // Cancel Button
    cancelBtn.addEventListener('click', () => {
        resetUI();
    });

    // Extract Text Button
    extractBtn.addEventListener('click', async () => {
        if (!currentFile) return;

        const formData = new FormData();
        formData.append('image', currentFile);
        formData.append('lang', langSelect.value);

        showLoading(true);
        updateStep(0); // Uploading

        try {
            // Simulate step progress for smoother UX
            setTimeout(() => updateStep(1), 1000); // Cleaning
            
            const response = await fetch(`${API_URL}/extract`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Failed to process image');

            updateStep(2); // Extracting
            const data = await response.json();
            
            setTimeout(() => {
                updateStep(3); // Finalizing
                setTimeout(() => displayResults(data), 500);
            }, 800);
            
        } catch (error) {
            console.error(error);
            alert('Error processing image. Please try again.');
            showLoading(false);
        }
    });

    function updateStep(index) {
        steps.forEach((step, i) => {
            step.classList.remove('active', 'completed');
            if (i < index) step.classList.add('completed');
            if (i === index) step.classList.add('active');
        });
    }

    function displayResults(data) {
        extractedTextarea.value = data.full_text;
        updateStats(); // Initial stats
        confidenceVal.textContent = `${data.average_confidence}%`;
        
        // Add error handling for the image
        cleanedPreview.onerror = () => {
            console.error("Failed to load enhanced image from:", cleanedPreview.src);
            cleanedPreview.src = imagePreview.src; // Fallback to original if enhanced fails
        };
        
        cleanedPreview.src = `${API_URL}${data.cleaned_image_url}?t=${new Date().getTime()}`;

        saveToHistory(data.full_text, data.average_confidence);

        showLoading(false);
        previewSection.classList.add('hidden');
        resultSection.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Real-time Stats
    extractedTextarea.addEventListener('input', updateStats);

    function updateStats() {
        const text = extractedTextarea.value.trim();
        const words = text ? text.split(/\s+/).length : 0;
        const chars = text.length;
        
        wordCountVal.textContent = words;
        charCountVal.textContent = chars;
    }

    // Copy to Clipboard
    copyBtn.addEventListener('click', () => {
        extractedTextarea.select();
        document.execCommand('copy');
        const originalContent = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied';
        copyBtn.style.borderColor = '#00b894';
        copyBtn.style.color = '#00b894';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalContent;
            copyBtn.style.borderColor = '#eee';
            copyBtn.style.color = '#2d3436';
        }, 2000);
    });

    // Download .txt
    downloadBtn.addEventListener('click', () => {
        const text = extractedTextarea.value;
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'scribe_extracted_text.txt';
        a.click();
        URL.revokeObjectURL(url);
    });

    // Try Again
    tryAgainBtn.addEventListener('click', () => {
        resetUI();
    });

    function resetUI() {
        currentFile = null;
        fileInput.value = '';
        uploadSection.classList.remove('hidden');
        previewSection.classList.add('hidden');
        resultSection.classList.add('hidden');
        extractedTextarea.value = '';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function showLoading(show) {
        if (show) {
            loadingOverlay.classList.remove('hidden');
        } else {
            loadingOverlay.classList.add('hidden');
        }
    }
});
