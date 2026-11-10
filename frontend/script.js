// ======================================================
// SENTIA AI - FIXED FRONTEND SCRIPT
// ======================================================

// ======================================================
// DOM ELEMENTS
// ======================================================

const landingPage    = document.getElementById('landingPage');
const chatInterface  = document.getElementById('chatInterface');
const startButton    = document.getElementById('startButton');
const backButton     = document.getElementById('backButton');
const messageInput   = document.getElementById('messageInput');
const sendButton     = document.getElementById('sendButton');
const voiceButton    = document.getElementById('voiceButton');
const cancelVoiceButton = document.getElementById('cancelVoiceButton');
const chatMessages   = document.getElementById('chatMessages');
const currentEmotionIcon        = document.getElementById('currentEmotionIcon');
const currentEmotionName        = document.getElementById('currentEmotionName');
const currentEmotionDescription = document.getElementById('currentEmotionDescription');
const emotionProbabilityBar     = document.getElementById('emotionProbabilityBar');
const emotionProbabilityText    = document.getElementById('emotionProbabilityText');

// ======================================================
// CONFIG
// ======================================================

const FLASK_API_URL = 'http://127.0.0.1:5000/chat';

// ======================================================
// STATE
// ======================================================

let conversationHistory = [];
let recognition         = null;
let mediaRecorder       = null;
let audioChunks         = [];
let isCancelled         = false;
let isRecording         = false;

// ======================================================
// INIT
// ======================================================

function initApp() {
    console.log("SENTIA Frontend Initialized");

    if (landingPage)   landingPage.style.display   = 'flex';
    if (chatInterface) chatInterface.style.display  = 'none';

    if (startButton) {
        startButton.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            showChatInterface();
        });
    }

    if (backButton) {
        backButton.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            showLandingPage();
        });
    }

    if (sendButton) {
        sendButton.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            handleSendText();
        });
    }

    if (voiceButton) {
        voiceButton.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            toggleVoiceInput();
        });
    }

    if (cancelVoiceButton) {
        cancelVoiceButton.addEventListener('click', function(e) {
            e.preventDefault(); e.stopPropagation();
            cancelVoiceInput();
        });
    }

    if (messageInput) {
        messageInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault(); e.stopPropagation();
                handleSendText();
            }
        });
    }

    setupSpeechRecognition();
}

// ======================================================
// SHOW CHAT
// ======================================================

function showChatInterface() {
    try {
        if (landingPage)   { landingPage.classList.add('hidden');    landingPage.style.display = 'none'; }
        if (chatInterface) { chatInterface.classList.remove('hidden'); chatInterface.style.display = 'flex'; }
        if (messageInput)  messageInput.focus();

        if (chatMessages && chatMessages.children.length === 0) {
            addMessage(
                "Hi there! 💜 I'm SENTIA, your emotional support companion. I'm here to listen — feel free to share anything on your mind.",
                'sentia'
            );
        }
    } catch (err) { console.error("showChatInterface Error:", err); }
}

// ======================================================
// SHOW LANDING
// ======================================================

function showLandingPage() {
    try {
        if (chatInterface) chatInterface.style.display = 'none';
        if (landingPage)   { landingPage.classList.remove('hidden'); landingPage.style.display = 'flex'; }
    } catch (err) { console.error("showLandingPage Error:", err); }
}

// ======================================================
// SPEECH RECOGNITION SETUP
// ======================================================

function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        console.warn("Speech recognition not supported");
        if (voiceButton) voiceButton.disabled = true;
        return;
    }

    recognition = new SpeechRecognition();
    recognition.lang            = 'en-US';
    recognition.interimResults  = true;
    recognition.continuous      = false;

    recognition.onresult = function(event) {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
            transcript += event.results[i][0].transcript;
        }
        if (messageInput) messageInput.value = transcript;
    };

    recognition.onend = function() {
        if (isCancelled) return;
        finishVoiceRecording();
    };

    recognition.onerror = function(event) {
        console.error("Speech recognition error:", event.error);
        isRecording = false;
        resetVoiceButton();
    };
}

// ======================================================
// TOGGLE VOICE INPUT
// ======================================================

async function toggleVoiceInput() {
    try {
        if (!recognition || isRecording) return;

        isCancelled  = false;
        audioChunks  = [];
        isRecording  = true;

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

        // ---------------------------------------------------
        // FIX: prefer audio/webm but tag it so backend knows
        // We collect raw audio chunks for emotion detection
        // ---------------------------------------------------
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
            ? 'audio/webm;codecs=opus'
            : MediaRecorder.isTypeSupported('audio/webm')
            ? 'audio/webm'
            : 'audio/ogg';

        mediaRecorder = new MediaRecorder(stream, { mimeType });

        mediaRecorder.ondataavailable = function(e) {
            if (e.data.size > 0) audioChunks.push(e.data);
        };

        mediaRecorder.start();
        recognition.start();

        if (voiceButton)      { voiceButton.classList.add('voice-active'); voiceButton.disabled = true; }
        if (cancelVoiceButton) cancelVoiceButton.style.display = 'flex';
        if (messageInput)      messageInput.placeholder = 'Listening...';

    } catch (err) {
        console.error("Voice Error:", err);
        isRecording = false;
        resetVoiceButton();
    }
}

// ======================================================
// FINISH VOICE RECORDING
// ======================================================

function finishVoiceRecording() {
    try {
        isRecording = false;

        const capturedText = messageInput ? messageInput.value.trim() : '';

        if (!mediaRecorder || mediaRecorder.state === 'inactive') {
            resetVoiceButton();
            if (capturedText) sendVoiceToBackend(capturedText, audioChunks.slice(), mediaRecorder ? mediaRecorder.mimeType : 'audio/webm');
            return;
        }

        // Capture mimeType before stopping
        const mimeType = mediaRecorder.mimeType;

        mediaRecorder.onstop = function() {
            mediaRecorder.stream.getTracks().forEach(t => t.stop());
            resetVoiceButton();
            if (capturedText) sendVoiceToBackend(capturedText, audioChunks.slice(), mimeType);
        };

        mediaRecorder.stop();

    } catch (err) {
        console.error("finishVoiceRecording Error:", err);
        isRecording = false;
        resetVoiceButton();
    }
}

// ======================================================
// CANCEL VOICE
// ======================================================

function cancelVoiceInput() {
    isCancelled = true;
    isRecording = false;

    try {
        if (recognition) {
            recognition.onend = null;
            recognition.stop();
            setTimeout(() => {
                if (recognition) {
                    recognition.onend = function() {
                        if (isCancelled) return;
                        finishVoiceRecording();
                    };
                }
            }, 500);
        }

        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
            mediaRecorder.stream.getTracks().forEach(t => t.stop());
            mediaRecorder.stop();
        }

        audioChunks = [];
        if (messageInput) messageInput.value = '';
        resetVoiceButton();

    } catch (err) {
        console.error("cancelVoiceInput Error:", err);
        resetVoiceButton();
    }
}

// ======================================================
// RESET VOICE BUTTON
// ======================================================

function resetVoiceButton() {
    if (voiceButton)      { voiceButton.classList.remove('voice-active'); voiceButton.innerHTML = '<i class="fas fa-microphone"></i>'; voiceButton.disabled = false; }
    if (cancelVoiceButton) cancelVoiceButton.style.display = 'none';
    if (messageInput)      messageInput.placeholder = 'Share your thoughts or feelings...';
}

// ======================================================
// HANDLE SEND TEXT
// ======================================================

function handleSendText() {
    if (!messageInput) return;
    const message = messageInput.value.trim();
    if (!message) return;
    sendTextToBackend(message);
}

// ======================================================
// SEND TEXT → BACKEND (JSON)
// ======================================================

function sendTextToBackend(message) {
    try {
        addMessage(message, 'user');
        conversationHistory.push({ sender: 'user', text: message, time: new Date().toISOString() });
        if (messageInput) messageInput.value = '';
        showTypingIndicator();

        fetch(FLASK_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                input_type: 'text',
                history: conversationHistory
            })
        })
        .then(function(res) {
            if (!res.ok) throw new Error('Server error: ' + res.status);
            return res.json();
        })
        .then(function(data) { handleBackendResponse(data); })
        .catch(function(err) {
            console.error("Text fetch error:", err);
            hideTypingIndicator();
            addMessage("I'm having trouble connecting right now. Please make sure the backend is running. 💜", 'sentia');
        });

    } catch (err) { console.error("sendTextToBackend Error:", err); }
}

// ======================================================
// SEND VOICE → BACKEND
// FIX: Send as FormData with BOTH the transcript text
//      AND the raw audio blob so backend can:
//        - use transcript for STT (skip re-transcription)
//        - use audio blob for voice emotion detection
// ======================================================

function sendVoiceToBackend(transcript, chunks, mimeType) {
    try {
        addMessage(transcript, 'user');
        conversationHistory.push({ sender: 'user', text: transcript, time: new Date().toISOString() });
        if (messageInput) messageInput.value = '';
        showTypingIndicator();

        // Determine file extension from mimeType
        const ext = mimeType.includes('ogg') ? 'ogg' : 'webm';

        // Build FormData with transcript + raw audio
        const audioBlob = new Blob(chunks, { type: mimeType });
        const formData  = new FormData();
        formData.append('transcript', transcript);
        formData.append('audio', audioBlob, 'recording.' + ext);
        formData.append('history', JSON.stringify(conversationHistory));

        fetch(FLASK_API_URL, {
            method: 'POST',
            body: formData   // No Content-Type header — browser sets multipart boundary automatically
        })
        .then(function(res) {
            if (!res.ok) throw new Error('Server error: ' + res.status);
            return res.json();
        })
        .then(function(data) { handleBackendResponse(data); })
        .catch(function(err) {
            console.error("Voice fetch error:", err);
            hideTypingIndicator();
            addMessage("Voice processing failed. Please try typing instead. 💜", 'sentia');
        });

    } catch (err) { console.error("sendVoiceToBackend Error:", err); }
}

// ======================================================
// HANDLE BACKEND RESPONSE
// ======================================================

function handleBackendResponse(data) {
    hideTypingIndicator();
    console.log("Backend Response:", data);

    if (!data) { addMessage("I received an empty response. Please try again.", 'sentia'); return; }

    const reply = (
        (typeof data.response === 'string' && data.response.trim()) ||
        (typeof data.message  === 'string' && data.message.trim())  ||
        (typeof data.reply    === 'string' && data.reply.trim())     ||
        ''
    );

    if (!reply) {
        console.warn("Empty reply from backend:", data);
        addMessage("I couldn't form a response. Could you try again?", 'sentia');
        return;
    }

    addMessage(reply, 'sentia');
    conversationHistory.push({ sender: 'sentia', text: reply, time: new Date().toISOString() });

    if (data.emotion) {
        updateEmotionDisplay(
            data.emotion.name        || 'Neutral',
            data.emotion.icon        || 'fa-meh',
            data.emotion.color       || '#8B5FBF',
            data.emotion.description || '',
            data.emotion.confidence  || 60
        );
    }
}

// ======================================================
// ADD MESSAGE
// ======================================================

function addMessage(text, sender) {
    if (!chatMessages) return;

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;

    const senderLabel = document.createElement('div');
    senderLabel.className   = 'message-sender';
    senderLabel.textContent = sender === 'user' ? 'You' : 'SENTIA';

    const messageText = document.createElement('div');
    messageText.className = 'message-text';
    if (sender === 'sentia') {
        messageText.innerHTML = text.replace(/\n/g, '<br>');
    } else {
        messageText.textContent = text;
    }

    const now     = new Date();
    const timeDiv = document.createElement('div');
    timeDiv.className   = 'message-time';
    timeDiv.textContent = now.getHours().toString().padStart(2,'0') + ':' + now.getMinutes().toString().padStart(2,'0');

    messageDiv.appendChild(senderLabel);
    messageDiv.appendChild(messageText);
    messageDiv.appendChild(timeDiv);
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ======================================================
// TYPING INDICATOR
// ======================================================

function showTypingIndicator() {
    const el = document.getElementById('typingIndicator');
    if (el) { el.style.display = 'block'; chatMessages.scrollTop = chatMessages.scrollHeight; }
}

function hideTypingIndicator() {
    const el = document.getElementById('typingIndicator');
    if (el) el.style.display = 'none';
}

// ======================================================
// UPDATE EMOTION DISPLAY
// ======================================================

function updateEmotionDisplay(emotionName, icon, color, description, confidence) {
    if (currentEmotionIcon)        { currentEmotionIcon.innerHTML = `<i class="fas ${icon}"></i>`; currentEmotionIcon.style.color = color; }
    if (currentEmotionName)          currentEmotionName.textContent        = emotionName;
    if (currentEmotionDescription)   currentEmotionDescription.textContent = description;
    if (emotionProbabilityBar)     { emotionProbabilityBar.style.width      = `${confidence}%`; emotionProbabilityBar.style.background = `linear-gradient(to right, ${color}, ${color}99)`; }
    if (emotionProbabilityText)      emotionProbabilityText.textContent     = `${confidence}% confidence`;
}

// ======================================================
// START
// ======================================================

document.addEventListener('DOMContentLoaded', initApp);
