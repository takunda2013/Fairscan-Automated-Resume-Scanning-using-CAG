let uploadedFiles = [];
let currentPage = 1;
const itemsPerPage = 5;

// Prevent default form submission and handle it manually
// document.getElementById('uploadForm').addEventListener('submit', function(e) {
//     e.preventDefault();
//     uploadFiles();  // Manually call the upload function
// });

// Trigger file picker when custom button is clicked
function triggerFileInput() {
    const input = document.getElementById('file-upload');
    input.click();
    input.addEventListener('change', uploadFiles);  // Trigger only on change
}
function fetchDocuments() {
    console.log("GETTING DOCS");

    fetch('/get-documents/', {
        method: 'GET',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Documents fetched:', data);
        if (data.files && Array.isArray(data.files)) {
            // Update the global uploadedFiles array with the fetched data
            uploadedFiles = data.files;
            
            // Reset to first page when documents are loaded
            currentPage = 1;
            console.log("GETTING DOCS " + uploadFiles.length);


            // Update the UI with the fetched documents
            updateDocumentList();

        } else {
            console.warn('No document data or invalid format returned from server');
        }
    })
    .catch(error => {
        console.error('Error fetching documents:', error);
    });
}

// Function to handle page load initialization
document.addEventListener('DOMContentLoaded', function () {
    // Setup delete button
    const deleteAllBtn = document.getElementById('deleteAllBtn');
    if (deleteAllBtn) {
        deleteAllBtn.addEventListener('click', deleteFiles);
    }

    // Setup upload button
    const uploadBtn = document.getElementById('uploadBtn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', triggerFileInput);
    }

    // Initial document fetch
    fetchDocuments();
});

// Update the uploadFiles function to fetch documents after upload
function uploadFiles() {
    console.log("executing");
    const input = document.getElementById('file-upload');
    
    if (input.files.length > 0) {
        const formData = new FormData();
        
        // First, validate the files before appending them to FormData
        for (let i = 0; i < input.files.length; i++) {
            const file = input.files[i];
            const fileType = file.type;

            // Check file type before uploading
            if (!fileType.includes('pdf') && !fileType.includes('word')) {
                alert('Please upload only PDF or DOCX files.');
                return;
            }

            formData.append('files', file);
        }

        // Add CSRF token to the formData
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        // Show loading indicator if you have one
        // document.getElementById('loading-indicator').style.display = 'block';

        fetch('/upload/', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Upload success:', data);
            
            // Instead of manually adding files, fetch the updated list from server
            fetchDocuments();
            
            // Hide loading indicator if you have one
            // document.getElementById('loading-indicator').style.display = 'none';
        })
        .catch(error => {
            console.error('Error uploading files:', error);
            alert('Error uploading files: ' + error.message);
            // Hide loading indicator if you have one
            // document.getElementById('loading-indicator').style.display = 'none';
        })
        .finally(() => {
            input.value = '';  // Clear the file input
        });
    }
}


function getCSRFToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split('; ');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].split('=');
        if (cookie[0] === name) {
            return decodeURIComponent(cookie[1]);
        }
    }
    return null;
}


function updateDocumentList() {
    const docList = document.getElementById('doc-list');
    const pagination = document.getElementById('pagination');
    
    // Clear existing items
    docList.innerHTML = '';
    pagination.innerHTML = '';
    
    // Calculate pagination
    const totalPages = Math.ceil(uploadedFiles.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, uploadedFiles.length);

    document.getElementById('total-documents').textContent = uploadedFiles.length;

    // Add current page items
    for (let i = startIndex; i < endIndex; i++) {
        const li = document.createElement('li');
        li.classList.add('document-item');
        
        const fileName = uploadedFiles[i].name;
        const fileId = uploadedFiles[i].id;

        // Accessibility attributes
        li.setAttribute('role', 'button');
        li.setAttribute('tabindex', '0');
        li.setAttribute('aria-label', `Open document ${fileName}`);
        
        // Create document elements
        const icon = document.createElement('span');
        icon.textContent = '📑';
        icon.classList.add('file-icon');
        
        const textNode = document.createElement('span');
        textNode.textContent = fileName;
        textNode.classList.add('file-name');
        
        const removeBtn = document.createElement('button');
        removeBtn.innerHTML = '&times;';
        removeBtn.classList.add('remove-btn');
        removeBtn.setAttribute('aria-label', `Remove document ${fileName}`);
        
        // Event handlers
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            removeDocument(i);
        });

        const handleClick = () => {
            console.log(`Opening document ${fileId}`);
            openDocument(fileId);
        };

        // Click handling
        li.addEventListener('click', handleClick);
        
        // Keyboard navigation
        li.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                handleClick();
            }
        });

        // Hover effects
        li.addEventListener('mouseenter', () => {
            li.style.backgroundColor = '#e0e0e0';
        });
        
        li.addEventListener('mouseleave', () => {
            li.style.backgroundColor = '#f5f5f5';
        });

        // Styles
        Object.assign(li.style, {
            cursor: 'pointer',
            backgroundColor: '#f5f5f5',
            padding: '8px',
            margin: '4px 0',
            borderRadius: '4px',
            transition: 'background-color 0.2s',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
        });

        // Structure
        li.append(icon, textNode, removeBtn);
        docList.appendChild(li);
    }

    // Pagination controls
    if (totalPages > 1) {
        const maxVisiblePages = 9; // Odd number for balanced display
        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

        // Adjust if we're at the end
        if (endPage - startPage < maxVisiblePages - 1) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        // Previous button
        if (currentPage > 1) {
            const prevBtn = createPaginationButton('Previous', () => {
                currentPage--;
                updateDocumentList();
            });
            prevBtn.classList.add('pagination-prev');
            pagination.appendChild(prevBtn);
        }

        // Page numbers
        for (let page = startPage; page <= endPage; page++) {
            const pageBtn = createPaginationButton(page, () => {
                currentPage = page;
                updateDocumentList();
            });
            if (page === currentPage) {
                pageBtn.classList.add('active');
            }
            pagination.appendChild(pageBtn);
        }

        // Next button
        if (currentPage < totalPages) {
            const nextBtn = createPaginationButton('Next', () => {
                currentPage++;
                updateDocumentList();
            });
            nextBtn.classList.add('pagination-next');
            pagination.appendChild(nextBtn);
        }
    }
}

// Helper function for pagination buttons
function createPaginationButton(text, onClick) {
    const btn = document.createElement('button');
    btn.textContent = text;
    btn.classList.add('pagination-btn');
    btn.addEventListener('click', onClick);
    return btn;
}

// Example openDocument implementation
function openDocument(fileId) {
    // Replace with your actual document opening logic
    console.log(`Attempting to open document ${fileId}`);
    window.open(`/document/${fileId}`, '_blank');
}

function removeDocument(index) {
    // Get the document ID from the uploadedFiles array
    const documentId = uploadedFiles[index].id;
    
    // Make sure we have a valid ID
    if (!documentId) {
        console.error('Cannot delete document: No document ID available');
        return;
    }
    
    // Confirm deletion with the user
    if (!confirm('Are you sure you want to delete this document?')) {
        return;
    }
    
    // Send delete request to the backend
    fetch(`/delete-document/${documentId}/`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Document deleted:', data);
        
        if (data.success) {
            // Remove from local array only after successful backend deletion
            uploadedFiles.splice(index, 1);
            
            // Re-render the document list
            updateDocumentList();
            
           
        } else {
            alert(`Error: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error deleting document:', error);
        alert('Error deleting document: ' + error.message);
    });
}
// Delete all documents
function deleteFiles(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    if (!confirm('Are you sure you want to delete ALL documents? This action cannot be undone.')) {
        return;
    }

    fetch('/delete-all-documents/', {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            uploadedFiles = [];
            updateDocumentList();
            alert('All documents have been deleted successfully.');
        } else {
            alert(`Error: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error deleting all documents:', error);
        alert('Error deleting all documents: ' + error.message);
    });
}








/////////////////////////////////////the other button


function getOneDocument() {
    
    document.getElementById('fileInput').click();
}

// Function to handle the selected file
// function handleFileSelect(event) {
//     const file = event.target.files[0];
//     if (file) {
//         alert(`File selected: ${file.name}`);
//         // Here you would typically handle the file upload
//         // For example: uploadFile(file);
//     }
// }


function uploadOntology(event) {
    console.log("executing");
        const formData = new FormData();
       
        const file = event.target.files[0];
        if (file) {

            const fileType = file.type;

            // Check file type before uploading
            if (!fileType.includes('pdf') && !fileType.includes('word')) {
                alert('Please upload only PDF or DOCX files.');
                return;
            }
            formData.append('files', file);

            // Here you would typically handle the file upload
            // For example: uploadFile(file);
        }

        // Add CSRF token to the formData
        formData.append('csrfmiddlewaretoken', getCSRFToken());

        fetch('/ontology/', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Upload success:', data);
            alert("Onology Document Uploaded Successfully");  // Show the response message
          
        })
        .catch(error => {
            console.error('Error uploading files:', error);
        });

    
}

        // Get the button element
const processBtn = document.getElementById('processBtn');
const spinner = processBtn.querySelector('.processing-spinner');
const processText = processBtn.querySelector('.process-text');
const originalText = processText.textContent;

// WebSocket connection for real-time updates
let chatSocket = null;
let totalDocs = 0;
let completedResumes = 0;

// Function to get CSRF token for Django
function getCSRFToken() {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
  return csrfToken ? csrfToken.value : null;
}

// Initialize WebSocket connection
function initWebSocket() {
  chatSocket = new WebSocket('ws://' + window.location.host + '/ws/scan/');

  chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    // Update progress data
    if (data.total_docs !== undefined) {
      totalDocs = data.total_docs;
    }
    
    if (data.graded !== undefined) {
      completedResumes = data.graded;
      
      // Check if processing is complete
      if (totalDocs > 0 && completedResumes >= totalDocs) {
        processingComplete();
      }
    }
  };

  chatSocket.onclose = function(e) {
    console.error('WebSocket closed unexpectedly');
    if (processBtn.classList.contains('processing')) {
      processingError();
    }
  };
}

// Function to call the Django process-batch endpoint
async function processResumeBatch() {
  try {
    const response = await fetch('/process-batch/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken(),
        'X-Requested-With': 'XMLHttpRequest'
      },
      credentials: 'same-origin',
      body: JSON.stringify({
        action: 'process_batch'
      })
    });

    const responseText = await response.text();
    console.log('Raw response:', responseText);

    if (!response.ok) {
      console.log('Server error response:', responseText);
      throw new Error(`HTTP error! status: ${response.status}, message: ${responseText}`);
    }

    try {
      const result = JSON.parse(responseText);
      return result;
    } catch (error) {
      console.error('JSON parsing failed. Response was:', responseText);
      throw new Error('Server returned invalid JSON');
    }
  } catch (error) {
    console.error('Network error:', error);
    throw error;
  }
}

function startProcessing() {
  processBtn.classList.add('processing');
  spinner.style.display = 'inline-block';
  processBtn.disabled = true;
  processText.textContent = 'Processing...';
  initWebSocket(); // Initialize WebSocket when processing starts
}

function processingComplete() {
  if (!processBtn.classList.contains('processing')) return;
  
  processText.textContent = 'Complete!';
  spinner.style.display = 'none';
  
  setTimeout(() => {
    processText.textContent = originalText;
    processBtn.classList.remove('processing');
    processBtn.disabled = false;
    if (chatSocket) chatSocket.close();
  }, 2000);
}

function processingError() {
  processText.textContent = 'Error!';
  spinner.style.display = 'none';
  
  setTimeout(() => {
    processText.textContent = originalText;
    processBtn.classList.remove('processing');
    processBtn.disabled = false;
    if (chatSocket) chatSocket.close();
  }, 3000);
  
  alert('Processing failed. Please try again.');
}

// Click handler with processing state
async function handleProcess() {
  try {
    startProcessing();
    const result = await processResumeBatch();
    
    // If the endpoint returns immediate completion (unlikely with WebSockets)
    if (result.success && result.completed && result.total_docs && 
        result.completed >= result.total_docs) {
      processingComplete();
    }
    
  } catch (error) {
    console.error('Processing failed:', error);
    processingError();
  }
}

// Add event listeners
processBtn.addEventListener('click', handleProcess);

processBtn.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    handleProcess();
  }
});
// // Make the main upload button work when DOM is loaded
// document.addEventListener('DOMContentLoaded', function() {
//     const mainUploadBtn = document.querySelector('header .btn');
//     if (mainUploadBtn) {
//         mainUploadBtn.addEventListener('click', getOneDocument);
//     }
// });