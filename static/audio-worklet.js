class ResamplingProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.targetRate = 16000;
        this.sourceRate = sampleRate; // provided by the browser
        this.ratio = this.sourceRate / this.targetRate;
        this.sourceOffset = 0;
        this.buffer = [];
    }

    process(inputs) {
        const input = inputs[0][0];
        if (!input || input.length === 0) return true;

        // Collect samples
        for (let i = 0; i < input.length; i++) {
            this.buffer.push(input[i]);
        }

        const out = [];

        // Loop while we have enough samples to interpolate (we need 2 samples for linear interp)
        while (this.sourceOffset + 1 < this.buffer.length) {
            const i = Math.floor(this.sourceOffset);
            const frac = this.sourceOffset - i;

            // Linear interpolation
            const val = (1 - frac) * this.buffer[i] + frac * this.buffer[i + 1];
            out.push(val);

            this.sourceOffset += this.ratio;
        }

        // Remove the samples we've fully moved past
        const consumeCount = Math.floor(this.sourceOffset);
        if (consumeCount > 0) {
            this.buffer = this.buffer.slice(consumeCount);
            this.sourceOffset -= consumeCount;
        }

        if (out.length > 0) {
            this.port.postMessage(out);
        }

        // Keep buffer size under control in case sourceOffset doesn't advance correctly
        if (this.buffer.length > 48000) { // ~1 second safety
            this.buffer = [];
            this.sourceOffset = 0;
        }

        return true;
    }
}

registerProcessor("resampling-processor", ResamplingProcessor);