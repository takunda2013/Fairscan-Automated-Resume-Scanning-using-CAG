document.addEventListener('DOMContentLoaded', function() {
            // WebSocket setup
            const fileSocket = new WebSocket('ws://' + window.location.host + '/ws/files/');
            const connectionStatus = document.getElementById('connection-status');
            // const resetButton = document.getElementById('reset-button');
            // const pauseButton = document.getElementById('pause-button');
            const table = document.getElementById('resultsTable');
            const tbody = table.querySelector('tbody');
            let isPaused = false;
            
            // paginationR configuration
            const rowsPerPage = 5;
            let currentPage = 1;

            // SEARCH =======================

            const searchInput = document.getElementById('searchInput');

            searchInput.addEventListener('input', function () {
                const filter = this.value.toLowerCase();
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

            
            // // WebSocket event handlers
            // fileSocket.onopen = function(e) {
            //     connectionStatus.textContent = 'WebSocket: Connected';
            //     connectionStatus.className = 'connected';
            // };
            
            // fileSocket.onclose = function(e) {
            //     connectionStatus.textContent = 'WebSocket: Disconnected';
            //     connectionStatus.className = 'disconnected';
            //     console.error('WebSocket connection closed unexpectedly');
            // };
            
            fileSocket.onerror = function(e) {
                console.error('WebSocket error:', e);
            };
            
            fileSocket.onmessage = function(e) {
                const data = JSON.parse(e.data);
                
                if (data.action === 'add_file' && !isPaused) {
                    // Add new file row to table
                    addFileToTable(data.file_data);
                    
                    // Update paginationR
                    updatepaginationR();
                    
                    // Show current page
                    showPage(currentPage);
                } else if (data.action === 'reset_table') {
                    // Clear table
                    tbody.innerHTML = '';
                    updatepaginationR();
                }
            };
            
            // // Button event handlers
            // resetButton.addEventListener('click', function() {
            //     fileSocket.send(JSON.stringify({
            //         'message': 'reset'
            //     }));
            // });
            
            // pauseButton.addEventListener('click', function() {
            //     isPaused = !isPaused;
            //     pauseButton.textContent = isPaused ? 'Resume' : 'Pause';
            // });
            
            // Table and paginationR functions
            function addFileToTable(fileData) {
                const row = document.createElement('tr');
                
                const nameCell = document.createElement('td');
                nameCell.textContent = fileData.file_name;
                
                const scoreCell = document.createElement('td');
                scoreCell.textContent = fileData.score;
                
                const linkCell = document.createElement('td');
                const link = document.createElement('a');
                link.href = 'document/' + 1;
                // window.open(`/document/${fileData.id}`, '_blank');

                link.textContent = 'View';
                link.target = '_blank';
                link.style.color= 'green'; 
                link.style.textDecoration = 'none';
                // link.addEventListener('click', function(e) {
                //     e.preventDefault();
                //     alert('Viewing file: ' + fileData.file_name);
                // });
                linkCell.appendChild(link);
                
                row.appendChild(nameCell);
                row.appendChild(scoreCell);
                row.appendChild(linkCell);
                
                tbody.appendChild(row);
            }
            
            function updatepaginationR() {
                const rows = tbody.querySelectorAll('tr');
                const totalPages = Math.ceil(rows.length / rowsPerPage);
                const paginationR = document.getElementById('paginationR');
                
                paginationR.innerHTML = '';
                
                // Previous button
                const prev = document.createElement('a');
                prev.href = '#';
                prev.innerHTML = '&laquo;';
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
                const rows = Array.from(tbody.querySelectorAll('tr'));
                const start = (page - 1) * rowsPerPage;
                const end = start + rowsPerPage;
                
                rows.forEach((row, index) => {
                    row.style.display = (index >= start && index < end) ? '' : 'none';
                });
                
                // Update active page in paginationR
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
            }
            
            // Initialize empty paginationR
            updatepaginationR();
        });




        