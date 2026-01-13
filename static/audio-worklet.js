class ResamplingProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.targetRate = 16000;
        this.sourceRate = sampleRate;
        this.ratio = this.sourceRate / this.targetRate;
        this.buffer = [];
        this.offset = 0;
    }

    process(inputs) {
        const input = inputs[0][0];
        if (!input) return true;

        for (let i = 0; i < input.length; i++) {
            this.buffer.push(input[i]);
        }

        const out = [];
        while (this.offset + this.ratio < this.buffer.length) {
            out.push(this.buffer[Math.floor(this.offset)]);
            this.offset += this.ratio;
        }

        this.buffer = this.buffer.slice(Math.floor(this.offset));
        this.offset -= Math.floor(this.offset);

        if (out.length) {
            this.port.postMessage(out);
        }
        return true;
    }
}

registerProcessor("resampling-processor", ResamplingProcessor);
// ================= END ====================