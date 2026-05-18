/**
 * Fankaar Digital — Jarvis Voice Interface
 * Implements Web Speech API for voice communication with Jon Snow (CEO)
 */

const micBtn = document.getElementById('mic-btn');
const transcript = document.getElementById('transcript');
const responseText = document.getElementById('response-text');
const arcReactor = document.querySelector('.arc-reactor');

// ── Voice Recognition Setup ──────────────────────────────────
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
        micBtn.classList.add('listening');
        transcript.textContent = "Listening...";
        transcript.classList.remove('waiting');
        animateReactor(true);
    };

    recognition.onresult = (event) => {
        const command = event.results[0][0].transcript;
        transcript.textContent = `"${command}"`;
        processCommand(command);
    };

    recognition.onspeechend = () => {
        recognition.stop();
        micBtn.classList.remove('listening');
        animateReactor(false);
    };

    recognition.onerror = (event) => {
        micBtn.classList.remove('listening');
        transcript.textContent = "Error occurred in recognition: " + event.error;
        animateReactor(false);
    };
} else {
    transcript.textContent = "Voice recognition not supported in this browser.";
    micBtn.disabled = true;
}

// ── Voice Synthesis ───────────────────────────────────────────
const synth = window.speechSynthesis;

function speak(text) {
    if (synth.speaking) {
        console.error('speechSynthesis.speaking');
        return;
    }
    const utterThis = new SpeechSynthesisUtterance(text);

    // Attempt to find a 'Jarvis-like' voice (deep, male, professional)
    const voices = synth.getVoices();
    const preferredVoice = voices.find(v => v.name.includes('Daniel') || v.name.includes('Google UK English Male'));
    if (preferredVoice) utterThis.voice = preferredVoice;

    utterThis.pitch = 0.9;
    utterThis.rate = 1.0;

    utterThis.onstart = () => {
        animateReactor(true, 'pulse');
    };

    utterThis.onend = () => {
        animateReactor(false);
    };

    synth.speak(utterThis);
}

// ── Command Processing ───────────────────────────────────────
async function processCommand(command) {
    responseText.textContent = "Processing...";

    try {
        const response = await fetch('/api/ceo/message', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: command })
        });

        const data = await response.json();
        responseText.textContent = data.response;
        speak(data.response);

    } catch (error) {
        console.error('Error:', error);
        responseText.textContent = "I'm sorry, sir. I'm having trouble connecting to the neural network.";
        speak("I'm sorry, sir. I'm having trouble connecting to the neural network.");
    }
}

// ── UI Effects ────────────────────────────────────────────────
function animateReactor(active, mode = 'rotate') {
    const rings = document.querySelectorAll('[class^="ring-"]');
    rings.forEach(ring => {
        if (active) {
            ring.style.boxShadow = mode === 'pulse' ? '0 0 30px var(--jarvis-blue)' : '0 0 15px var(--jarvis-blue)';
            ring.style.opacity = '1';
        } else {
            ring.style.boxShadow = '0 0 10px var(--jarvis-glow)';
            ring.style.opacity = '0.5';
        }
    });
}

// ── Event Listeners ───────────────────────────────────────────
micBtn.addEventListener('click', () => {
    if (recognition) {
        recognition.start();
    }
});

// Randomize stats for flavor
setInterval(() => {
    document.getElementById('cpu-load').textContent = (Math.random() * 5 + 2).toFixed(1) + '%';
}, 3000);
