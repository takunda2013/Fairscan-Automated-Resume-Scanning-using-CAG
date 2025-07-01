const chatSocket = new WebSocket('ws://' + window.location.host + '/ws/scan/');

console.log(window.location.host);
const progressElement = document.getElementById('real-time-progress');
const pendingElement = document.getElementById('real-time-pending');
const successElement = document.getElementById('real-time-completed');

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    // Update progress display
    if (data.counter !== undefined) {
        progressElement.textContent = `${data.counter}%`;
        pendingElement.textContent =`${data.pending}`
        successElement.textContent =`${data.graded}`
        

        
        // Optional: Add visual progress bar animation
        // progressElement.style.width = `${data.counter}%`;
    }
    
    // Handle messages
    if (data.message !== undefined) {
        console.log('System message:', data.message);
    }
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

// Send message to server
function sendMessage(message) {
    chatSocket.send(JSON.stringify({
        'message': message
    }));
};


