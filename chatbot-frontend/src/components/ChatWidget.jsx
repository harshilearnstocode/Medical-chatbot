import React, { useState, useEffect, useRef } from "react";
import "./ChatWidget.css";

function ChatWidget() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const [examplePrompts, setExamplePrompts] = useState([
    "I have a headache and fever. What should I do?",
    "What department should I visit for chest pain?",
    "I feel dizziness and nausea, what might be the cause?",
    "How can I tell if my cough is serious?",
  ]);
  const [showExamples, setShowExamples] = useState(true);
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);

  useEffect(() => {
    if (
      !("webkitSpeechRecognition" in window || "SpeechRecognition" in window)
    ) {
      return;
    }

    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setListening(true);
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      setListening(false);
    };
    recognition.onerror = () => setListening(false);
    recognition.onend = () => setListening(false);

    recognitionRef.current = recognition;
  }, []);

  const toggleListening = () => {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    if (listening) {
      recognition.stop();
      setListening(false);
    } else {
      recognition.start();
      setListening(true);
    }
  };

  const sendMessage = async (prompt) => {
    const messageToSend = prompt || input;
    if (!messageToSend.trim()) return;

    const userMsg = { sender: "user", text: messageToSend };
    setMessages((prev) => [...prev, userMsg, { sender: "bot", text: "..." }]);
    setInput("");
    setShowExamples(false);

    try {
      const res = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: [...messages, userMsg] }),
      });
      const data = await res.json();

      let botResponse = "";
      if (typeof data.response === "string") {
        botResponse = data.response;
      } else if (data.response && typeof data.response.answer === "string") {
        botResponse = data.response.answer;
      } else {
        botResponse = "⚠️ Sorry, I couldn't understand the response.";
      }

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { sender: "bot", text: botResponse };
        return updated;
      });
    } catch (error) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          sender: "bot",
          text: "⚠️ Error communicating with the server.",
        };
        return updated;
      });
    }
  };

  const endChat = () => {
    setMessages([]);
    setInput("");
    setShowExamples(true);
  };

  return (
    <div className="chat-widget">
      <button
        className="toggle-button"
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle chat"
      >
        🩺
      </button>

      {isOpen && (
        <div className="chat-popup">
          <div className="chat-header">
            <span>🩺 Medical Assistant Chatbot</span>
            <button className="close-btn" onClick={() => setIsOpen(false)}>
              ✖
            </button>
          </div>

          <div className="chat-box">
            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.sender}`}>
                <div className="bubble">
                  <strong>{msg.sender === "user" ? "You" : "Bot"}:</strong>{" "}
                  {msg.text}
                </div>
              </div>
            ))}

            {showExamples && examplePrompts.length > 0 && (
              <div className="example-prompts">
                {examplePrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    className="example-btn"
                    onClick={() => sendMessage(prompt)}
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="input-area">
            <input
              type="text"
              placeholder="Describe your symptoms or ask a medical question..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              aria-label="Chat input"
              autoComplete="off"
            />
            <button
              className={`mic-btn ${listening ? "listening" : ""}`}
              onClick={toggleListening}
              aria-label={listening ? "Stop voice input" : "Start voice input"}
            >
              🎤
            </button>
            <button
              className="send-btn"
              onClick={() => sendMessage()}
              aria-label="Send message"
            >
              ➤
            </button>
          </div>

          {/* End Chat Button */}
          {messages.length > 0 && (
            <button className="end-chat-btn" onClick={endChat}>
              🛑 End Chat
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default ChatWidget;
