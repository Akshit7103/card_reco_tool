document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('upload-form');
    const fileInput = document.getElementById('file-input');
    const resultsDiv = document.getElementById('results');

    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            alert('Please select a file first');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        // Show loading message
        resultsDiv.innerHTML = '<p>Processing image...</p>';
        resultsDiv.classList.add('show');

        // Send file to server
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            displayResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
            resultsDiv.innerHTML = '<p>Error processing image. Please try again.</p>';
        });
    });

    function displayResults(data) {
        if (data.error) {
            resultsDiv.innerHTML = `<p>Error: ${data.error}</p>`;
            return;
        }

        let html = '<h3>Recognition Results:</h3>';
        html += `<p><strong>Detected Text:</strong> ${data.text || 'No text detected'}</p>`;
        
        if (data.card_info) {
            html += '<h4>Card Information:</h4>';
            html += `<p><strong>Type:</strong> ${data.card_info.type || 'Unknown'}</p>`;
            html += `<p><strong>Number:</strong> ${data.card_info.number || 'Not detected'}</p>`;
        }

        resultsDiv.innerHTML = html;
    }
});