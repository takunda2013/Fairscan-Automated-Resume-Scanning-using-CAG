// JavaScript for PDF generation and document history panel

document.addEventListener('DOMContentLoaded', function() {
    // Generate PDF on page load
    // generatePDF();
    
    // Load document history
    loadDocumentHistory();
    
    // Set interval to refresh document history every 30 seconds (adjust as needed)
    setInterval(loadDocumentHistory, 30000);
});

/**
 * Function to generate a new PDF document
 */
function generatePDF() {
    // Show loading indicator
    const rightPanel = document.querySelector('.right-panel');
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'history-item loading';
    loadingDiv.innerHTML = '<span>Just now</span>Generating new PDF document...';
    
    // Add loading indicator at the top of history panel
    if (rightPanel.querySelector('.history-title')) {
        rightPanel.insertBefore(loadingDiv, rightPanel.querySelector('.history-title').nextSibling);
    } else {
        rightPanel.appendChild(loadingDiv);
    }
    
    // Make AJAX call to generate PDF endpoint
    fetch('/generate_pdf_api/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Remove loading indicator
        if (loadingDiv) {
            loadingDiv.remove();
        }
        
        // Add the new document to history
        if (data.success) {
            addDocumentToHistory({
                id: data.document_id,
                title: data.document_title,
                timestamp: 'Just now',
                action: 'Generated new document'
            });
            
            // Show success message
            showNotification('Welcome ✔', 'success');
        } else {
            showNotification('Failed to generate document: ' + data.error, 'error');
        }
        
        // Refresh document history
        loadDocumentHistory();
    })
    .catch(error => {
        console.error('Error generating PDF:', error);
        
        // Remove loading indicator
        if (loadingDiv) {
            loadingDiv.remove();
        }
        
        showNotification('Error generating document: ' + error.message, 'error');
    });
}

/**
 * Function to load document history from the server
 */
function loadDocumentHistory() {

    console.log("FETCHING HISTORY DOCS TOKEN " + getCSRFToken());
    fetch('/get_documents_api/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        credentials: 'same-origin'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to load document history');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            updateDocumentHistoryPanel(data.documents);
        } else {
            console.error('Server returned error:', data.error);
        }
    })
    .catch(error => {
        console.error('Error loading document history:', error);
    });
}

/**
 * Function to update the document history panel with real data
 * @param {Array} documents - Array of document objects
 */
function updateDocumentHistoryPanel(documents) {
    const rightPanel = document.querySelector('.right-panel');
    
    // Keep the title, remove all history items
    const historyItems = rightPanel.querySelectorAll('.history-item:not(.loading)');
    historyItems.forEach(item => item.remove());
    
    if (documents.length === 0) {
        // Show empty state
        const emptyDiv = document.createElement('div');
        emptyDiv.className = 'history-item empty';
        emptyDiv.textContent = 'No documents processed yet.';
        rightPanel.appendChild(emptyDiv);
        return;
    }
    
    // Add document history items
    documents.forEach(doc => {
        addDocumentToHistory({
            id: doc.id,
            title: doc.title,
            timestamp: formatTimestamp(doc.created_at),
            // filePath: doc.file_path
        }, false); // Don't prepend, add in chronological order
    });
}

/**
 * Add a single document to the history panel
 * @param {Object} doc - Document object
 * @param {boolean} prepend - Whether to add at the top (true) or bottom (false)
 */
function addDocumentToHistory(doc, prepend = true) {
    const rightPanel = document.querySelector('.right-panel');
    
    const historyItem = document.createElement('div');
    historyItem.className = 'history-item';
    historyItem.dataset.documentId = doc.id;
    
    // Make the whole item clickable
    historyItem.style.cursor = 'pointer';
    historyItem.addEventListener('click', function() {
        viewDocument(doc.id, doc.filePath);
    });
    
    // Create timestamp span
    const timeSpan = document.createElement('span');
    timeSpan.textContent = doc.timestamp;
    
    // Create document information text
    const textNode = document.createTextNode(
        ` ${doc.action || 'Processed document'} "${doc.title}"`
    );
    
    // Add elements to the history item
    historyItem.appendChild(timeSpan);
    historyItem.appendChild(textNode);
    
    // Add to the panel
    if (prepend) {
        // Add after the title
        const title = rightPanel.querySelector('.history-title');
        if (title && title.nextSibling) {
            rightPanel.insertBefore(historyItem, title.nextSibling);
        } else {
            rightPanel.appendChild(historyItem);
        }
    } else {
        // Add at the end
        rightPanel.appendChild(historyItem);
    }
}

/**
 * View a document in the document viewer
 * @param {number} documentId - ID of the document to view
 * @param {string} filePath - Path to the document file
 */
function viewDocument(documentId, filePath) {
    // Navigate to the document viewer page or open PDF directly

        // window.location.href = `/processed-document-viewer/${documentId}/`;
        window.open(`/processed-document-viewer/${documentId}/`, '_blank');

    // if (filePath) {
    //     // Construct the media URL for the PDF
    //     const mediaUrl = `/media/${filePath}`;
    //     window.open(mediaUrl, '_blank');
    // } else {
    //     // Fallback to document viewer page
    //     window.location.href = `/document-viewer/${documentId}/`;
    // }
}

/**
 * Format timestamp into a readable format
 * @param {string} timestamp - ISO timestamp from the server
 * @returns {string} - Formatted timestamp
 */
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    
    // If today, show "Today, HH:MM AM/PM"
    if (date.toDateString() === now.toDateString()) {
        return `Today, ${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
    }
    
    // If yesterday, show "Yesterday, HH:MM AM/PM"
    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
        return `Yesterday, ${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
    }
    
    // Otherwise show date and time
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`;
}

/**
 * Get CSRF token for Django
 * @returns {string} - CSRF token
 */
function getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length);
        }
    }
    return '';
}

/**
 * Show a notification message
 * @param {string} message - Message to display
 * @param {string} type - Message type ('success', 'error', 'info')
 */
function showNotification(message, type = 'info') {
    // Check if notification container exists, if not create it
    let notificationContainer = document.getElementById('notification-container');
    
    if (!notificationContainer) {
        notificationContainer = document.createElement('div');
        notificationContainer.id = 'notification-container';
        notificationContainer.style.position = 'fixed';
        notificationContainer.style.top = '20px';
        notificationContainer.style.right = '20px';
        notificationContainer.style.zIndex = '9999';
        document.body.appendChild(notificationContainer);
    }
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Style the notification
    notification.style.padding = '12px 16px';
    notification.style.marginBottom = '10px';
    notification.style.borderRadius = '4px';
    notification.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    notification.style.backgroundColor = type === 'success' ? '#4CAF50' : 
                                         type === 'error' ? '#F44336' : '#2196F3';
    notification.style.color = 'white';
    notification.style.minWidth = '250px';
    
    // Add to container
    notificationContainer.appendChild(notification);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.5s ease';
        
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 5000);
}