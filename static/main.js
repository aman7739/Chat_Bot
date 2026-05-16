const API_URL = "/chat";
const FEEDBACK_URL = "/feedback";
const LEAD_URL = "/submit-lead";
const APPOINTMENT_URL = "/book-appointment";
const WHATSAPP_NUMBER = "916200615848";

// DOM References
const messagesContainer = document.getElementById("chat-messages");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const voiceBtn = document.getElementById("voice-btn");
const langToggle = document.getElementById("lang-toggle");
const historyBtn = document.getElementById("history-btn");
const historySidebar = document.getElementById("history-sidebar");
const closeHistoryBtn = document.getElementById("close-history");
const historyList = document.getElementById("history-list");
const clearHistoryBtn = document.getElementById("clear-history");
const ttsToggle = document.getElementById("tts-toggle");

// State
let currentLanguage = "en";
let chatHistory = JSON.parse(localStorage.getItem("chatHistory")) || [];
let conversationHistory = [];
let sessionId = "user_" + Date.now();
let ttsEnabled = false;

// Voice Recognition
let recognition = null;
if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  
  recognition.onstart = () => {
    voiceBtn.classList.add("listening");
    voiceBtn.textContent = "🔴";
  };
  
  recognition.onend = () => {
    voiceBtn.classList.remove("listening");
    voiceBtn.textContent = "🎤";
  };
  
  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    userInput.value = transcript;
    sendMessage();
  };
  
  recognition.onerror = (event) => {
    console.error("Speech recognition error:", event.error);
    voiceBtn.classList.remove("listening");
    voiceBtn.textContent = "🎤";
  };
}

voiceBtn.addEventListener("click", () => {
  if (!recognition) {
    alert("Voice input not supported in your browser. Please use Chrome or Edge.");
    return;
  }
  
  if (voiceBtn.classList.contains("listening")) {
    recognition.stop();
  } else {
    recognition.lang = currentLanguage === "hi" ? "hi-IN" : "en-US";
    recognition.start();
  }
});

// Text-to-Speech Toggle
ttsToggle.addEventListener("change", (e) => {
  ttsEnabled = e.target.checked;
  const msg = currentLanguage === "hi" 
    ? (ttsEnabled ? "Voice replies enabled" : "Voice replies disabled")
    : (ttsEnabled ? "Voice replies enabled" : "Voice replies disabled");
  addSystemMessage(msg);
});

// ✨ Text-to-Speech Function with FEMALE VOICE
function speakText(text) {
  if (!ttsEnabled) return;
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = currentLanguage === "hi" ? "hi-IN" : "en-US";
    utterance.rate = 0.9;
    
    // Select female voice
    const voices = window.speechSynthesis.getVoices();
    let femaleVoice = null;
    
    if (currentLanguage === "hi") {
      // Hindi female voice
      femaleVoice = voices.find(voice => 
        voice.lang.includes('hi') && voice.name.toLowerCase().includes('female')
      ) || voices.find(voice => voice.lang.includes('hi'));
    } else {
      // English female voice
      femaleVoice = voices.find(voice => 
        voice.lang.includes('en') && (
          voice.name.includes('Female') || 
          voice.name.includes('female') ||
          voice.name.includes('Samantha') ||
          voice.name.includes('Victoria') ||
          voice.name.includes('Karen') ||
          voice.name.includes('Moira') ||
          voice.name.includes('Tessa') ||
          voice.name.includes('Zira')
        )
      ) || voices.find(voice => voice.lang.includes('en-US'));
    }
    
    if (femaleVoice) {
      utterance.voice = femaleVoice;
    }
    
    // Higher pitch for feminine sound
    utterance.pitch = 1.2;
    
    window.speechSynthesis.speak(utterance);
  }
}

// Language Toggle
langToggle.addEventListener("change", (e) => {
  currentLanguage = e.target.checked ? "hi" : "en";
  userInput.placeholder = currentLanguage === "hi" 
    ? "Apna sawal type karein..." 
    : "Type your question...";
  
  const langMsg = currentLanguage === "hi" 
    ? "Bhasha Hindi mein badal di gayi hai" 
    : "Language switched to English";
  addSystemMessage(langMsg);
});

// History Sidebar
historyBtn.addEventListener("click", () => {
  historySidebar.classList.toggle("open");
  loadHistorySidebar();
});

closeHistoryBtn.addEventListener("click", () => {
  historySidebar.classList.remove("open");
});

clearHistoryBtn.addEventListener("click", () => {
  if (confirm("Are you sure you want to clear all chat history?")) {
    chatHistory = [];
    localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
    loadHistorySidebar();
  }
});

function loadHistorySidebar() {
  historyList.innerHTML = "";
  
  if (chatHistory.length === 0) {
    historyList.innerHTML = "<p style='text-align:center; color:#888; padding:20px;'>No chat history yet</p>";
    return;
  }
  
  chatHistory.slice().reverse().forEach((chat) => {
    const item = document.createElement("div");
    item.classList.add("history-item");
    const time = new Date(chat.timestamp).toLocaleString();
    item.innerHTML = `
      <div class="history-time">${time}</div>
      <div class="history-text">${chat.message}</div>
    `;
    item.onclick = () => {
      userInput.value = chat.message;
      historySidebar.classList.remove("open");
      userInput.focus();
    };
    historyList.appendChild(item);
  });
}

function saveToHistory(message) {
  chatHistory.push({ timestamp: new Date().toISOString(), message: message });
  if (chatHistory.length > 50) chatHistory = chatHistory.slice(-50);
  localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addSystemMessage(text) {
  const wrapper = document.createElement("div");
  wrapper.style.textAlign = "center";
  wrapper.style.margin = "10px 0";
  wrapper.style.fontSize = "12px";
  wrapper.style.color = "#888";
  wrapper.textContent = text;
  messagesContainer.appendChild(wrapper);
  scrollToBottom();
}

function addUserMessage(text) {
  const wrapper = document.createElement("div");
  wrapper.classList.add("message-row", "user");
  wrapper.innerHTML = `
    <div class="avatar-circle user-avatar">🙂</div>
    <div class="msg user-msg"></div>
  `;
  wrapper.querySelector(".msg").textContent = text;
  messagesContainer.appendChild(wrapper);
  scrollToBottom();
  conversationHistory.push({ role: "user", content: text });
}

function addBotMessage(text, userMsg, pdfSuggestions = []) {
  const wrapper = document.createElement("div");
  wrapper.classList.add("message-row", "bot");
  wrapper.innerHTML = `
    <div class="avatar-circle bot-avatar">🤖</div>
    <div class="msg bot-msg"></div>
  `;
  wrapper.querySelector(".msg").textContent = text;
  messagesContainer.appendChild(wrapper);
  
  addFeedbackButtons(userMsg, text);
  
  if (pdfSuggestions.length > 0) {
    addPDFButtons(pdfSuggestions);
  }
  
  scrollToBottom();
  conversationHistory.push({ role: "assistant", content: text });
  
  // Speak with female voice
  speakText(text);
}

function addFeedbackButtons(userMsg, botReply) {
  const feedbackContainer = document.createElement("div");
  feedbackContainer.classList.add("feedback-buttons");
  
  const helpfulBtn = document.createElement("button");
  helpfulBtn.classList.add("feedback-btn");
  helpfulBtn.innerHTML = "👍";
  helpfulBtn.title = "Helpful";
  
  const notHelpfulBtn = document.createElement("button");
  notHelpfulBtn.classList.add("feedback-btn");
  notHelpfulBtn.innerHTML = "👎";
  notHelpfulBtn.title = "Not Helpful";
  
  helpfulBtn.onclick = () => sendFeedback(userMsg, botReply, "helpful", helpfulBtn, notHelpfulBtn);
  notHelpfulBtn.onclick = () => sendFeedback(userMsg, botReply, "not_helpful", helpfulBtn, notHelpfulBtn);
  
  feedbackContainer.appendChild(helpfulBtn);
  feedbackContainer.appendChild(notHelpfulBtn);
  messagesContainer.appendChild(feedbackContainer);
  scrollToBottom();
}

async function sendFeedback(userMsg, botReply, feedbackType, btn1, btn2) {
  try {
    await fetch(FEEDBACK_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userMsg, answer: botReply, feedback: feedbackType })
    });
    
    if (feedbackType === "helpful") {
      btn1.classList.add("selected");
      btn1.style.background = "#10ac84";
    } else {
      btn2.classList.add("selected");
      btn2.style.background = "#ee5a6f";
    }
    
    btn1.disabled = true;
    btn2.disabled = true;
    
    const thankYouMsg = currentLanguage === "hi" 
      ? "Feedback ke liye dhanyavaad!" 
      : "Thanks for your feedback!";
    
    setTimeout(() => {
      const thankYou = document.createElement("div");
      thankYou.style.marginLeft = "40px";
      thankYou.style.fontSize = "12px";
      thankYou.style.color = "#888";
      thankYou.style.marginBottom = "10px";
      thankYou.textContent = thankYouMsg;
      messagesContainer.appendChild(thankYou);
      scrollToBottom();
    }, 300);
  } catch (error) {
    console.error("Feedback error:", error);
  }
}

function addPDFButtons(pdfTypes) {
  const container = document.createElement("div");
  container.classList.add("suggestion-container");
  
  const pdfLabels = {
    "brochure": currentLanguage === "hi" ? "📄 Admission Brochure" : "📄 Admission Brochure",
    "fees": currentLanguage === "hi" ? "💰 Fee Structure PDF" : "💰 Fee Structure PDF",
    "transport": currentLanguage === "hi" ? "🚌 Transport Routes PDF" : "🚌 Transport Routes PDF"
  };
  
  pdfTypes.forEach(type => {
    const btn = document.createElement("a");
    btn.classList.add("suggestion-btn");
    btn.textContent = pdfLabels[type];
    btn.href = `/download/${type}`;
    btn.target = "_blank";
    btn.download = true;
    container.appendChild(btn);
  });
  
  messagesContainer.appendChild(container);
  scrollToBottom();
}

function addWhatsAppButton() {
  const container = document.createElement("div");
  container.classList.add("suggestion-container");
  
  const btn = document.createElement("button");
  btn.classList.add("suggestion-btn");
  btn.innerHTML = "💬 Chat on WhatsApp";
  btn.onclick = () => {
    const msg = currentLanguage === "hi" 
      ? "Namaste! Main college ke baare mein jaankari chahta hoon."
      : "Hello! I need information about admission.";
    window.open(`https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(msg)}`, '_blank');
  };
  
  container.appendChild(btn);
  messagesContainer.appendChild(container);
  scrollToBottom();
}

function showLeadForm() {
  const formHTML = `
    <div class="lead-form-overlay" id="lead-overlay">
      <div class="lead-form">
        <h3>${currentLanguage === "hi" ? "अपनी जानकारी दें" : "Get a Callback"}</h3>
        <p>${currentLanguage === "hi" ? "हमारी टीम आपसे संपर्क करेगी" : "Our team will contact you"}</p>
        <input type="text" id="lead-name" placeholder="${currentLanguage === "hi" ? "नाम" : "Your Name"}" />
        <input type="tel" id="lead-phone" placeholder="${currentLanguage === "hi" ? "फोन नंबर" : "Phone Number"}" />
        <input type="text" id="lead-course" placeholder="${currentLanguage === "hi" ? "कौनसा कोर्स?" : "Interested Course"}" />
        <button onclick="submitLead()">${currentLanguage === "hi" ? "भेजें" : "Submit"}</button>
        <button onclick="closeLeadForm()" class="close-form">${currentLanguage === "hi" ? "बंद करें" : "Cancel"}</button>
      </div>
    </div>
  `;
  
  document.body.insertAdjacentHTML('beforeend', formHTML);
}

async function submitLead() {
  const name = document.getElementById("lead-name").value;
  const phone = document.getElementById("lead-phone").value;
  const course = document.getElementById("lead-course").value;
  
  if (!name || !phone) {
    alert(currentLanguage === "hi" ? "कृपया सभी जानकारी भरें" : "Please fill all fields");
    return;
  }
  
  try {
    const res = await fetch(LEAD_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, phone, course })
    });
    
    if (res.ok) {
      closeLeadForm();
      addSystemMessage(currentLanguage === "hi" 
        ? "धन्यवाद! हम जल्द ही आपसे संपर्क करेंगे।" 
        : "Thank you! We'll contact you soon.");
    }
  } catch (err) {
    console.error(err);
  }
}

function closeLeadForm() {
  const overlay = document.getElementById("lead-overlay");
  if (overlay) overlay.remove();
}

function showAppointmentForm() {
  const formHTML = `
    <div class="lead-form-overlay" id="appointment-overlay">
      <div class="lead-form">
        <h3>${currentLanguage === "hi" ? "कैंपस विजिट बुक करें" : "Book Campus Visit"}</h3>
        <input type="text" id="apt-name" placeholder="${currentLanguage === "hi" ? "नाम" : "Your Name"}" />
        <input type="tel" id="apt-phone" placeholder="${currentLanguage === "hi" ? "फोन नंबर" : "Phone Number"}" />
        <input type="date" id="apt-date" />
        <select id="apt-time">
          <option value="10:00 AM">10:00 AM</option>
          <option value="12:00 PM">12:00 PM</option>
          <option value="2:00 PM">2:00 PM</option>
          <option value="4:00 PM">4:00 PM</option>
        </select>
        <button onclick="submitAppointment()">${currentLanguage === "hi" ? "बुक करें" : "Book Now"}</button>
        <button onclick="closeAppointmentForm()" class="close-form">${currentLanguage === "hi" ? "बंद करें" : "Cancel"}</button>
      </div>
    </div>
  `;
  
  document.body.insertAdjacentHTML('beforeend', formHTML);
}

async function submitAppointment() {
  const name = document.getElementById("apt-name").value;
  const phone = document.getElementById("apt-phone").value;
  const date = document.getElementById("apt-date").value;
  const time = document.getElementById("apt-time").value;
  
  if (!name || !phone || !date) {
    alert(currentLanguage === "hi" ? "कृपया सभी जानकारी भरें" : "Please fill all fields");
    return;
  }
  
  try {
    const res = await fetch(APPOINTMENT_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, phone, date, time })
    });
    
    if (res.ok) {
      closeAppointmentForm();
      addSystemMessage(currentLanguage === "hi" 
        ? "आपकी अपॉइंटमेंट बुक हो गई है!" 
        : "Your appointment has been booked!");
    }
  } catch (err) {
    console.error(err);
  }
}

function closeAppointmentForm() {
  const overlay = document.getElementById("appointment-overlay");
  if (overlay) overlay.remove();
}

function showTyping() {
  const wrapper = document.createElement("div");
  wrapper.classList.add("message-row", "bot");
  wrapper.id = "typing-indicator";
  wrapper.innerHTML = `
    <div class="avatar-circle bot-avatar">🤖</div>
    <div class="msg bot-msg">
      <span class="typing-dots">
        <span></span><span></span><span></span>
      </span>
    </div>
  `;
  messagesContainer.appendChild(wrapper);
  scrollToBottom();
}

function removeTyping() {
  const typing = document.getElementById("typing-indicator");
  if (typing) typing.remove();
}

function addSuggestionButtons() {
  const suggestions = currentLanguage === "hi" 
    ? ["💰 Fees", "📅 Admission", "📚 Courses", "🚌 Transport"]
    : ["💰 Fees", "📅 Admission", "📚 Courses", "🚌 Transport"];

  const container = document.createElement("div");
  container.classList.add("suggestion-container");

  suggestions.forEach(text => {
    const btn = document.createElement("button");
    btn.classList.add("suggestion-btn");
    btn.textContent = text;
    btn.onclick = () => {
      userInput.value = text;
      sendMessage();
      container.remove();
    };
    container.appendChild(btn);
  });

  messagesContainer.appendChild(container);
  scrollToBottom();
}

function addFallbackSuggestionButtons() {
  const container = document.createElement("div");
  container.classList.add("suggestion-container");

  const options = [
    { label: "💰 Fees", text: "fees" },
    { label: "📚 Courses", text: "courses" },
    { label: "📞 Contact", text: "contact" },
    { label: "📝 Get Callback", action: showLeadForm },
    { label: "💬 WhatsApp", action: addWhatsAppButton }
  ];

  options.forEach(option => {
    const btn = document.createElement("button");
    btn.classList.add("suggestion-btn");
    btn.textContent = option.label;
    btn.onclick = () => {
      if (option.action) {
        option.action();
      } else {
        userInput.value = option.text;
        sendMessage();
      }
      container.remove();
    };
    container.appendChild(btn);
  });

  messagesContainer.appendChild(container);
  scrollToBottom();
}

async function sendMessage(event) {
  if (event) event.preventDefault();
  const text = userInput.value.trim();
  if (!text) return;

  addUserMessage(text);
  saveToHistory(text);
  userInput.value = "";
  userInput.focus();
  sendBtn.disabled = true;

  const existingSuggestions = document.querySelector(".suggestion-container");
  if (existingSuggestions) existingSuggestions.remove();

  showTyping();

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        message: text,
        language: currentLanguage,
        session_id: sessionId
      })
    });

    if (!response.ok) throw new Error("Server error: " + response.status);

    const data = await response.json();
    const botReply = data.answer || "Sorry, I didn't understand that.";

    setTimeout(() => {
      removeTyping();
      addBotMessage(botReply, text, data.pdf_suggestions || []);
      sendBtn.disabled = false;

      if (data.fallback === true) {
        addFallbackSuggestionButtons();
      }

      if (conversationHistory.length >= 6) {
        setTimeout(() => {
          addSystemMessage(currentLanguage === "hi" 
            ? "क्या आप admission के लिए callback चाहते हैं?" 
            : "Would you like a callback for admission?");
          showLeadForm();
        }, 2000);
      }
    }, 1100);

  } catch (error) {
    console.error(error);
    setTimeout(() => {
      removeTyping();
      const errorMsg = currentLanguage === "hi"
        ? "Maaf karein! Server se connect nahi ho pa raha."
        : "Oops! There was a problem connecting to the server.";
      addBotMessage(errorMsg, text);
      sendBtn.disabled = false;
    }, 1100);
  }
}

sendBtn.addEventListener("click", sendMessage);
userInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") sendMessage(event);
});

// Load voices when available
if ('speechSynthesis' in window) {
  speechSynthesis.onvoiceschanged = () => {
    const voices = speechSynthesis.getVoices();
    console.log('Available voices:', voices.map(v => v.name));
  };
}

window.addEventListener("load", () => {
  setTimeout(() => {
    const welcomeMsg = currentLanguage === "hi"
      ? "Namaste! Main aapki college enquiry assistant hoon. Aap mujhse fees, courses, timings aur admission ke baare mein pooch sakte hain."
      : "Hello! I am your college enquiry assistant. You can ask me about fees, courses, timings, and admission.";
    
    addBotMessage(welcomeMsg, "");
    addSuggestionButtons();
    
    setTimeout(() => {
      addWhatsAppButton();
      const container = document.createElement("div");
      container.classList.add("suggestion-container");
      const visitBtn = document.createElement("button");
      visitBtn.classList.add("suggestion-btn");
      visitBtn.innerHTML = "📅 Book Campus Visit";
      visitBtn.onclick = showAppointmentForm;
      container.appendChild(visitBtn);
      messagesContainer.appendChild(container);
      scrollToBottom();
    }, 1000);
  }, 200);
});