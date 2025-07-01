const chatSocket = new WebSocket('ws://' + window.location.host + '/ws/scan/dashboard/');

console.log(window.location.host);
const processedResumes = document.getElementById('real-time-processed-resumes');
const fairnessScore = document.getElementById('real-time-fairness-score');
const demographicParity = document.getElementById('real-time-demographic-parity');
const criticalBiases = document.getElementById('real-time-critical-biases');

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    

    // Update progress display
    if (data.counter !== undefined) {
        console.log("DASHBOARD METRICS " + data.counter)

        processedResumes.textContent = `${data.counter}`;
        fairnessScore.textContent = `${data.counter}`;
        demographicParity.textContent = `${data.counter}%`;
        criticalBiases.textContent = `${data.counter}`;
        
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


