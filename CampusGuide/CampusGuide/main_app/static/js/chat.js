function sendMessage() {

    const input = document.getElementById("userInput");
    const message = input.value.trim();

    if (message === "") return;

    const chatBox = document.getElementById("chatBox");

    chatBox.appendChild(createMessageElement("user", message));
    input.value = "";

    // Use relative path to avoid i18n redirect issues (POST -> GET)
    let chatbotUrl = "/chatbot/";
    // If the URL has a language prefix (e.g. /en/chat/), use the same for the chatbot
    const pathParts = window.location.pathname.split('/');
    if (pathParts.length > 1 && pathParts[1].length === 2) {
        chatbotUrl = "/" + pathParts[1] + "/chatbot/";
    }

    fetch(chatbotUrl, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: "message=" + encodeURIComponent(message)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        chatBox.appendChild(createMessageElement("bot", data.response));
        chatBox.scrollTop = chatBox.scrollHeight;
        // Save Q&A to history sidebar
        if (typeof addToHistory === "function") {
            addToHistory(message, data.response);
        }
    })
    .catch(error => console.error(error));
}

let speechRecognition = null;
let isListening = false;
let finalSpeechText = "";
let currentUtterance = null;
let ttsAudioQueue = [];
let isPlayingFallbackTTS = false;

function getRecognitionLocale() {
    const pathParts = window.location.pathname.split("/");
    const lang = (pathParts[1] || "en").toLowerCase();
    if (lang === "gu") return "gu-IN";
    if (lang === "hi") return "hi-IN";
    return "en-US";
}

function updateVoiceStatus(text) {
    const status = document.getElementById("voiceStatus");
    if (status) status.textContent = text || "";
}

function getSpeechLocale() {
    return getRecognitionLocale();
}

function detectSpeechLocaleFromText(text) {
    const t = (text || "").trim();
    // Gujarati Unicode block
    if (/[\u0A80-\u0AFF]/.test(t)) return "gu-IN";
    // Devanagari Unicode block (Hindi)
    if (/[\u0900-\u097F]/.test(t)) return "hi-IN";
    return getSpeechLocale();
}

function normalizeSpeechText(text) {
    return (text || "")
        .replace(/```[\s\S]*?```/g, " ")
        .replace(/`([^`]+)`/g, "$1")
        .replace(/\*\*([^*]+)\*\*/g, "$1")
        .replace(/\*([^*]+)\*/g, "$1")
        .replace(/#{1,6}\s*/g, "")
        .replace(/\[(.*?)\]\((.*?)\)/g, "$1")
        .replace(/[•➤✅❌🤖🎓💰📖🏛️]/g, " ")
        .replace(/\s+/g, " ")
        .trim();
}

function pickVoiceForLocale(locale) {
    const voices = window.speechSynthesis.getVoices() || [];
    if (!voices.length) return null;
    const localePrefix = locale.split("-")[0].toLowerCase();
    if (localePrefix === "gu") {
        return (
            voices.find(v => /gu(-|_|$)/i.test(v.lang || "")) ||
            voices.find(v => /gujarati/i.test(v.name || "")) ||
            null
        );
    }
    if (localePrefix === "hi") {
        return (
            voices.find(v => /hi(-|_|$)/i.test(v.lang || "")) ||
            voices.find(v => /hindi/i.test(v.name || "")) ||
            null
        );
    }
    return (
        voices.find(v => (v.lang || "").toLowerCase() === locale.toLowerCase()) ||
        voices.find(v => (v.lang || "").toLowerCase().startsWith(localePrefix)) ||
        null
    );
}

function splitTextForTTS(text, maxLen = 180) {
    const words = (text || "").split(" ");
    const chunks = [];
    let current = "";
    for (const w of words) {
        if (!w) continue;
        if ((current + " " + w).trim().length > maxLen) {
            if (current.trim()) chunks.push(current.trim());
            current = w;
        } else {
            current = (current + " " + w).trim();
        }
    }
    if (current.trim()) chunks.push(current.trim());
    return chunks;
}

function playFallbackTTS(text, locale, buttonEl) {
    const lang = locale.startsWith("gu") ? "gu" : (locale.startsWith("hi") ? "hi" : "en");
    const chunks = splitTextForTTS(text);
    if (!chunks.length) return;

    if (isPlayingFallbackTTS) {
        ttsAudioQueue = [];
        isPlayingFallbackTTS = false;
    }

    isPlayingFallbackTTS = true;
    if (buttonEl) {
        buttonEl.textContent = "Stop";
        buttonEl.dataset.speaking = "true";
    }
    updateVoiceStatus("Speaking...");

    ttsAudioQueue = chunks.map(chunk => {
        const q = encodeURIComponent(chunk);
        return `https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl=${lang}&q=${q}`;
    });

    const audio = new Audio();
    audio.crossOrigin = "anonymous";

    const playNext = () => {
        if (!isPlayingFallbackTTS || !ttsAudioQueue.length) {
            isPlayingFallbackTTS = false;
            if (buttonEl) {
                buttonEl.textContent = "Speak";
                buttonEl.dataset.speaking = "false";
            }
            updateVoiceStatus("");
            return;
        }
        audio.src = ttsAudioQueue.shift();
        audio.play().catch(() => {
            isPlayingFallbackTTS = false;
            if (buttonEl) {
                buttonEl.textContent = "Speak";
                buttonEl.dataset.speaking = "false";
            }
            updateVoiceStatus("Gujarati/Hindi TTS fallback failed.");
        });
    };

    audio.onended = playNext;
    audio.onerror = () => {
        isPlayingFallbackTTS = false;
        if (buttonEl) {
            buttonEl.textContent = "Speak";
            buttonEl.dataset.speaking = "false";
        }
        updateVoiceStatus("Gujarati/Hindi TTS fallback failed.");
    };
    playNext();

    if (buttonEl) {
        buttonEl.onclick = () => {
            isPlayingFallbackTTS = false;
            ttsAudioQueue = [];
            audio.pause();
            audio.currentTime = 0;
            buttonEl.textContent = "Speak";
            buttonEl.dataset.speaking = "false";
            updateVoiceStatus("");
            buttonEl.onclick = null;
            buttonEl.addEventListener("click", () => speakMessage(text, buttonEl), { once: true });
        };
    }
}

function speakMessage(text, buttonEl) {
    if (!("speechSynthesis" in window)) {
        updateVoiceStatus("Text-to-speech is not supported in this browser.");
        return;
    }
    const cleaned = normalizeSpeechText(text);
    if (!cleaned) return;

    if (buttonEl && buttonEl.dataset.speaking === "true") {
        window.speechSynthesis.cancel();
        buttonEl.dataset.speaking = "false";
        buttonEl.textContent = "Speak";
        updateVoiceStatus("");
        currentUtterance = null;
        return;
    }

    window.speechSynthesis.cancel();
    currentUtterance = null;

    const utterance = new SpeechSynthesisUtterance(cleaned);
    const detectedLocale = detectSpeechLocaleFromText(cleaned);
    utterance.lang = detectedLocale;
    let matchedVoice = pickVoiceForLocale(detectedLocale);

    // Local fallback only (no network): Gujarati -> Hindi voice -> browser default voice.
    if (!matchedVoice && detectedLocale.startsWith("gu")) {
        matchedVoice = pickVoiceForLocale("hi-IN");
        if (matchedVoice) {
            utterance.lang = "hi-IN";
        }
    }
    if (!matchedVoice && detectedLocale.startsWith("hi")) {
        matchedVoice = pickVoiceForLocale("en-US");
    }
    if (matchedVoice) {
        utterance.voice = matchedVoice;
    } else {
        updateVoiceStatus("No suitable TTS voice found in browser.");
    }
    utterance.rate = 1;
    utterance.pitch = 1;

    utterance.onstart = () => {
        if (buttonEl) {
            buttonEl.textContent = "Stop";
            buttonEl.dataset.speaking = "true";
        }
        updateVoiceStatus("Speaking...");
    };
    utterance.onend = () => {
        if (buttonEl) {
            buttonEl.textContent = "Speak";
            buttonEl.dataset.speaking = "false";
        }
        updateVoiceStatus("");
        currentUtterance = null;
    };
    utterance.onerror = () => {
        if (buttonEl) {
            buttonEl.textContent = "Speak";
            buttonEl.dataset.speaking = "false";
        }
        updateVoiceStatus("Unable to speak this message.");
        currentUtterance = null;
    };

    currentUtterance = utterance;
    window.speechSynthesis.speak(utterance);
}

function toggleVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const voiceBtn = document.getElementById("voiceBtn");
    const input = document.getElementById("userInput");

    if (!SpeechRecognition) {
        updateVoiceStatus("Voice input is not supported in this browser.");
        return;
    }

    if (!speechRecognition) {
        speechRecognition = new SpeechRecognition();
        speechRecognition.lang = getRecognitionLocale();
        speechRecognition.interimResults = true;
        speechRecognition.continuous = false;

        speechRecognition.onstart = () => {
            isListening = true;
            finalSpeechText = "";
            if (voiceBtn) voiceBtn.classList.add("listening");
            updateVoiceStatus("Listening...");
        };

        speechRecognition.onresult = (event) => {
            let interimText = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const chunk = event.results[i][0].transcript;
                if (event.results[i].isFinal) {
                    finalSpeechText += " " + chunk;
                } else {
                    interimText += chunk;
                }
            }
            const transcript = (finalSpeechText + " " + interimText).trim();
            if (transcript) {
                input.value = transcript;
            }
        };

        speechRecognition.onerror = () => {
            updateVoiceStatus("Microphone error. Please try again.");
        };

        speechRecognition.onend = () => {
            isListening = false;
            if (voiceBtn) voiceBtn.classList.remove("listening");
            updateVoiceStatus("");
            if ((input.value || "").trim()) {
                sendMessage();
            }
        };
    }

    if (isListening) {
        speechRecognition.stop();
    } else {
        speechRecognition.lang = getRecognitionLocale();
        speechRecognition.start();
    }
}

function handleEnter(event) {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
}

function createMessageElement(type, text) {
    const wrapper = document.createElement("div");
    wrapper.className = type === "user" ? "user-msg" : "bot-msg";

    const bubble = document.createElement("div");
    bubble.className = "message-bubble";

    const icon = document.createElement("span");
    icon.textContent = type === "user" ? "" : "🤖";

    const paragraph = document.createElement("p");
    paragraph.textContent = text;

    const actions = document.createElement("div");
    actions.className = "message-actions";

    const copyButton = document.createElement("button");
    copyButton.type = "button";
    copyButton.textContent = "Copy";
    copyButton.addEventListener("click", () => copyMessage(text, copyButton));

    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.textContent = "Edit";
    editButton.addEventListener("click", () => editMessage(text));

    const speakButton = document.createElement("button");
    speakButton.type = "button";
    speakButton.textContent = "Speak";
    speakButton.addEventListener("click", () => speakMessage(text, speakButton));

    actions.appendChild(copyButton);
    actions.appendChild(editButton);
    actions.appendChild(speakButton);

    bubble.appendChild(icon);
    bubble.appendChild(paragraph);
    bubble.appendChild(actions);
    wrapper.appendChild(bubble);

    return wrapper;
}

async function copyMessage(text, buttonEl) {
    let copied = false;
    try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(text);
            copied = true;
        }
    } catch (err) {
        console.error(err);
    }

    if (!copied) {
        const textarea = document.createElement("textarea");
        textarea.value = text;
        textarea.setAttribute("readonly", "");
        textarea.style.position = "fixed";
        textarea.style.opacity = "0";
        document.body.appendChild(textarea);
        textarea.select();
        copied = document.execCommand("copy");
        document.body.removeChild(textarea);
    }

    if (buttonEl) {
        const original = buttonEl.textContent;
        buttonEl.textContent = copied ? "Copied" : "Failed";
        setTimeout(() => {
            buttonEl.textContent = original;
        }, 900);
    }
}

function editMessage(text) {
    const input = document.getElementById("userInput");
    input.value = text;
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
}

function addActionsToExistingMessage(messageEl) {
    if (!messageEl || messageEl.querySelector(".message-actions")) return;
    const textNode = messageEl.querySelector("p");
    if (!textNode) return;

    const text = textNode.textContent || "";
    const actions = document.createElement("div");
    actions.className = "message-actions";

    const copyButton = document.createElement("button");
    copyButton.type = "button";
    copyButton.textContent = "Copy";
    copyButton.addEventListener("click", () => copyMessage(text, copyButton));

    const editButton = document.createElement("button");
    editButton.type = "button";
    editButton.textContent = "Edit";
    editButton.addEventListener("click", () => editMessage(text));

    const speakButton = document.createElement("button");
    speakButton.type = "button";
    speakButton.textContent = "Speak";
    speakButton.addEventListener("click", () => speakMessage(text, speakButton));

    actions.appendChild(copyButton);
    actions.appendChild(editButton);
    actions.appendChild(speakButton);

    // Existing welcome bot message does not use .message-bubble wrapper.
    if (messageEl.querySelector(".message-bubble")) {
        messageEl.querySelector(".message-bubble").appendChild(actions);
    } else {
        messageEl.appendChild(actions);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const existingMessages = document.querySelectorAll(".bot-msg, .user-msg");
    existingMessages.forEach(addActionsToExistingMessage);
    updateVoiceStatus("");
});

function endChat() {
    // Mark that we are intentionally leaving to feedback
    window._endingChat = true;
    window.location.href = "/feedback/";
}

/* ===== Intercept browser back button → redirect to feedback ===== */
(function () {
    // Push an extra history entry so "back" stays on this page first
    window.history.pushState({ chatPage: true }, "", window.location.href);

    window.addEventListener("popstate", function () {
        // User pressed back → redirect to feedback (same as End Chat)
        window._endingChat = true;
        window.location.href = "/feedback/";
    });
})();

function getCookie(name) {
    let cookieValue = null;

    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');

        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();

            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }

    return cookieValue;
}

