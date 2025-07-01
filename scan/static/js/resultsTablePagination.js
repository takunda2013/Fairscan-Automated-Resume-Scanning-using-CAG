document.addEventListener('DOMContentLoaded', function() {
    // WebSocket setup
    const fileSocket = new WebSocket('ws://' + window.location.host + '/ws/files/');
    const connectionStatus = document.getElementById('connection-status');
    const table = document.getElementById('resultsTable');
    const tbody = table.querySelector('tbody');
    let isPaused = false;
    
    // Pagination configuration
    const rowsPerPage = 5;
    let currentPage = 1;

    // SEARCH =======================
    const searchInput = document.getElementById('searchInput');
    let currentSearchFilter = '';

    searchInput.addEventListener('input', function () {
        const filter = this.value.toLowerCase();
        currentSearchFilter = filter; // Store current filter
        const rows = Array.from(tbody.querySelectorAll('tr'));

        let visibleCount = 0;
        rows.forEach(row => {
            const nameCell = row.cells[0].textContent.toLowerCase();
            const scoreCell = row.cells[1].textContent.toLowerCase();
            if (nameCell.includes(filter) || scoreCell.includes(filter)) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        // Disable pagination if searching
        const paginationR = document.getElementById('paginationR');
        if (filter.trim() !== '') {
            paginationR.style.display = 'none';
        } else {
            paginationR.style.display = '';
            showPage(currentPage);
        }
    });

    // WebSocket event handlers - UNCOMMENTED AND IMPROVED
    fileSocket.onopen = function(e) {
        console.log('WebSocket connected successfully');
        if (connectionStatus) {
            connectionStatus.textContent = 'WebSocket: Connected';
            connectionStatus.className = 'connected';
        }
    };
    
    fileSocket.onclose = function(e) {
        console.error('WebSocket connection closed:', e.code, e.reason);
        if (connectionStatus) {
            connectionStatus.textContent = 'WebSocket: Disconnected';
            connectionStatus.className = 'disconnected';
        }
        
        // Attempt to reconnect after 3 seconds
        setTimeout(function() {
            console.log('Attempting to reconnect...');
            location.reload(); // Simple reconnection strategy
        }, 3000);
    };
    
    fileSocket.onerror = function(e) {
        console.error('WebSocket error:', e);
        if (connectionStatus) {
            connectionStatus.textContent = 'WebSocket: Error';
            connectionStatus.className = 'error';
        }
    };
    
    fileSocket.onmessage = function(e) {
        console.log('Received WebSocket message:', e.data); // Debug log
        
        try {
            const data = JSON.parse(e.data);
            
            if (data.action === 'add_file' && !isPaused) {
                console.log('Adding file to table:', data.file_data); // Debug log
                
                // Add new file row to table at the TOP
                addFileToTable(data.file_data);
                
                // Reset to page 1 to show the newest item
                currentPage = 1;
                
                // Update pagination
                updatePagination();
                
                // Handle visibility based on current state
                handleNewRowVisibility();
                
            } else if (data.action === 'reset_table') {
                console.log('Resetting table'); // Debug log
                // Clear table
                tbody.innerHTML = '';
                currentPage = 1; // Reset to first page
                updatePagination();
            }
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };
    
    // Table and pagination functions
    function addFileToTable(fileData) {
        const row = document.createElement('tr');
        
        // Add a data attribute for easier identification
        row.setAttribute('data-file-id', fileData.id);
        row.setAttribute('data-added-time', new Date().toISOString());
        
        const nameCell = document.createElement('td');
        nameCell.textContent = fileData.file_name;
        
        const scoreCell = document.createElement('td');
        scoreCell.textContent = fileData.score;
        
        const linkCell = document.createElement('td');
        const link = document.createElement('a');
        
        // Extract file ID properly
        let fileId = fileData.id;
        if (typeof fileId === 'string' && fileId.startsWith('file_')) {
            fileId = fileId.replace('file_', '');
        }
        
        link.href = 'processed-document-viewer/' + fileId;
        link.textContent = 'View';
        link.target = '_blank';
        link.style.color = 'green'; 
        link.style.textDecoration = 'none';
        
        linkCell.appendChild(link);
        
        row.appendChild(nameCell);
        row.appendChild(scoreCell);
        row.appendChild(linkCell);
        
        // CRITICAL: Add to the TOP of the table (newest first)
        if (tbody.firstChild) {
            tbody.insertBefore(row, tbody.firstChild);
        } else {
            tbody.appendChild(row);
        }
        
        console.log('File added to TOP of table:', fileData.file_name);
        
        // Add a brief highlight animation to new row
        row.style.backgroundColor = '#e8f5e8';
        setTimeout(() => {
            row.style.backgroundColor = '';
        }, 2000);
    }
    
    function handleNewRowVisibility() {
        // Always reset to page 1 when new item is added to show it immediately
        currentPage = 1;
        
        // If we're searching, apply the search filter to all rows
        if (currentSearchFilter.trim() !== '') {
            const rows = Array.from(tbody.querySelectorAll('tr'));
            rows.forEach(row => {
                const nameCell = row.cells[0].textContent.toLowerCase();
                const scoreCell = row.cells[1].textContent.toLowerCase();
                if (nameCell.includes(currentSearchFilter) || scoreCell.includes(currentSearchFilter)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        } else {
            // If not searching, show page 1 to display the newest items
            showPage(1);
        }
    }
    
    function updatePagination() {
        // Only consider rows that are not hidden by search
        const allRows = Array.from(tbody.querySelectorAll('tr'));
        const visibleRows = allRows.filter(row => 
            currentSearchFilter.trim() === '' || row.style.display !== 'none'
        );
        
        const totalPages = Math.ceil(visibleRows.length / rowsPerPage);
        const paginationR = document.getElementById('paginationR');
        
        if (!paginationR) return; // Safety check
        
        paginationR.innerHTML = '';
        
        if (totalPages <= 1) return; // Don't show pagination for 1 or 0 pages
        
        // Previous button
        const prev = document.createElement('a');
        prev.href = '#';
        prev.innerHTML = '&laquo;';
        prev.className = currentPage === 1 ? 'disabled' : '';
        prev.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage > 1) {
                currentPage--;
                showPage(currentPage);
            }
        });
        paginationR.appendChild(prev);
        
        // Page numbers
        for (let i = 1; i <= totalPages; i++) {
            const link = document.createElement('a');
            link.href = '#';
            link.innerText = i;
            if (i === currentPage) {
                link.classList.add('active');
            }
            link.addEventListener('click', function(e) {
                e.preventDefault();
                currentPage = i;
                showPage(currentPage);
            });
            paginationR.appendChild(link);
        }
        
        // Next button
        const next = document.createElement('a');
        next.href = '#';
        next.innerHTML = '&raquo;';
        next.className = currentPage === totalPages ? 'disabled' : '';
        next.addEventListener('click', function(e) {
            e.preventDefault();
            if (currentPage < totalPages) {
                currentPage++;
                showPage(currentPage);
            }
        });
        paginationR.appendChild(next);
    }
    
    function showPage(page) {
        // Only consider visible rows (not hidden by search)
        const allRows = Array.from(tbody.querySelectorAll('tr'));
        const visibleRows = allRows.filter(row => 
            currentSearchFilter.trim() === '' || row.style.display !== 'none'
        );
        
        const start = (page - 1) * rowsPerPage;
        const end = start + rowsPerPage;
        
        // Hide all rows first
        allRows.forEach(row => {
            row.style.display = 'none';
        });
        
        // Show only the rows for current page
        visibleRows.slice(start, end).forEach(row => {
            row.style.display = '';
        });
        
        // If we're searching, re-apply search filter visibility
        if (currentSearchFilter.trim() !== '') {
            visibleRows.slice(start, end).forEach(row => {
                const nameCell = row.cells[0].textContent.toLowerCase();
                const scoreCell = row.cells[1].textContent.toLowerCase();
                if (!nameCell.includes(currentSearchFilter) && !scoreCell.includes(currentSearchFilter)) {
                    row.style.display = 'none';
                }
            });
        }
        
        // Update active page in pagination
        const pageLinks = document.querySelectorAll('#paginationR a');
        pageLinks.forEach((link, index) => {
            // Skip first (prev) and last (next) links
            if (index > 0 && index < pageLinks.length - 1) {
                if (index === page) {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            }
        });
        
        console.log(`Showing page ${page}, rows ${start}-${end-1} of ${visibleRows.length} visible rows`);
    }
    
    // Initialize empty pagination
    updatePagination();
    
    // Test connection on load
    console.log('WebSocket state:', fileSocket.readyState);
});