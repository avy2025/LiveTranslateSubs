const socket = io({
    transports: ["websocket"],
    upgrade: false
});
let audioContext;
let scriptProcessor;
let mediaStream;
let isListening = false;

const toggleBtn = document.getElementById('toggle-mic');
const subtitlesArea = document.getElementById('subtitles-area');
const latencyVal = document.getElementById('latency-val');
const bufferVal = document.getElementById('buffer-val');
const modelBadge = document.getElementById('model-badge');
const deviceBadge = document.getElementById('device-badge');
const langBadge = document.getElementById('language-badge');

const hardwareBadge = document.getElementById('hardware-badge');

socket.on('status', (data) => {
    modelBadge.textContent = data.model.toUpperCase();
    deviceBadge.textContent = data.device.toUpperCase();
    if (data.ram) {
        hardwareBadge.textContent = `${data.ram.toFixed(1)}GB RAM`;
    }
    console.log("System status:", data);
});

socket.on('subtitle_update', (data) => {
    if (subtitlesArea.querySelector('.placeholder')) {
        subtitlesArea.innerHTML = '';
    }

    let item = subtitlesArea.querySelector('.subtitle-item.partial');

    if (!item || data.type === 'committed') {
        if (item) item.classList.remove('partial');
        item = document.createElement('div');
        item.className = 'subtitle-item' + (data.type === 'partial' ? ' partial' : '');
        subtitlesArea.appendChild(item);
    }

    item.innerHTML = `
        <p class="translated">${data.translated}${data.type === 'partial' ? '...' : ''}</p>
        <p class="original">${data.original}</p>
    `;

    // Auto scroll to bottom
    const container = document.getElementById('subtitles-container');
    container.scrollTop = container.scrollHeight;

    // Update metrics
    latencyVal.textContent = data.latency;
    bufferVal.textContent = data.buffer_size;
});

toggleBtn.addEventListener('click', async () => {
    if (!isListening) {
        await startStreaming();
    } else {
        stopStreaming();
    }
});

async function startStreaming() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Your browser does not support microphone access in this context. Please ensure you are using 'localhost' or HTTPS.");
        return;
    }

    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const source = audioContext.createMediaStreamSource(mediaStream);

        await audioContext.audioWorklet.addModule('/static/audio-worklet.js');
        const workletNode = new AudioWorkletNode(audioContext, 'audio-processor');

        workletNode.port.onmessage = (event) => {
            const audioData = event.data;
            socket.emit('audio_data', Array.from(audioData));
        };

        source.connect(workletNode);
        workletNode.connect(audioContext.destination);

        isListening = true;
        toggleBtn.textContent = 'Stop Microphone';
        toggleBtn.classList.add('active');
        socket.emit('toggle_microphone', { active: true });

        console.log("Streaming started");
    } catch (err) {
        console.error("Error starting stream:", err);
        alert(`Could not access microphone. ${err.name}: ${err.message}`);
    }
}

function stopStreaming() {
    if (mediaStream) {
        mediaStream.getTracks().forEach(track => track.stop());
    }
    if (audioContext) {
        audioContext.close();
    }
    isListening = false;
    toggleBtn.textContent = 'Start Microphone';
    toggleBtn.classList.remove('active');
    socket.emit('toggle_microphone', { active: false });
    console.log("Streaming stopped");
}
