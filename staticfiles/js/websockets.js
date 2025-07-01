const chatSocket = new WebSocket('ws://' + window.location.host + '/ws/scan/');

console.log(window.location.host);
chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    
    // Handle incoming message
    if (data.message !== undefined) {
        console.log('Received message:', data.message);
    }
    
    // Handle counter updates
    if (data.counter !== undefined) {
        console.log('Counter value:', data.counter);
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