class AudioProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.buffer = [];
        this.bufferThreshold = 16000; // ~1 second at 16kHz
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (input.length > 0) {
            const channelData = input[0];

            // Append samples to internal buffer
            for (let i = 0; i < channelData.length; i++) {
                this.buffer.push(channelData[i]);
            }

            // Emit only when buffer threshold is reached
            if (this.buffer.length >= this.bufferThreshold) {
                this.port.postMessage(new Float32Array(this.buffer));
                this.buffer = [];
            }
        }
        return true;
    }
}

registerProcessor('audio-processor', AudioProcessor);
