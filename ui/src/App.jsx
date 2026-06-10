import { useState, useRef, useEffect, useCallback } from 'react';
import axios from 'axios';
import Particles from "react-tsparticles";
import { loadSlim } from "tsparticles-slim";
import './index.css';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your AI Assistant. I can provide facts about HDFC Mutual Funds.', type: 'greeting' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const particlesInit = useCallback(async engine => {
    await loadSlim(engine);
  }, []);

  const quickActions = [
    "What is the exit load for HDFC Defence Fund?",
    "List the top holdings of HDFC Gold ETF.",
    "Tell me the AUM of HDFC Sensex Index Fund."
  ];

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Transform markdown links to HTML links
  const formatContent = (text) => {
    // E.g., [[1]](https://...) -> <a href="..." target="_blank">[1]</a>
    let html = text.replace(/\[\[(.*?)\]\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">[$1]</a>');
    // Basic newline replacement
    html = html.replace(/\n/g, '<br/>');
    return { __html: html };
  };

  const handleSend = async (text) => {
    if (!text.trim()) return;
    
    const userMsg = { role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/query', { query: text });
      
      const assistantMsg = { 
        role: 'assistant', 
        content: response.data.answer,
        intent: response.data.intent,
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error communicating with the server.', isError: true }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Particles 
        id="tsparticles"
        init={particlesInit}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: "100%",
          height: "100%",
          zIndex: 0,
        }}
        options={{
            background: {
              color: { value: "#000000" }, // Pitch black background
            },
            fpsLimit: 60,
            interactivity: {
              events: {
                onHover: { 
                  enable: true, 
                  mode: "grab",
                  parallax: { enable: true, force: 60, smooth: 10 } // Adds 3D depth effect
                },
                resize: true,
              },
              modes: {
                grab: { distance: 200, links: { opacity: 0.8, color: "#1e3a8a" } },
              },
            },
            particles: {
              color: { value: ["#3b82f6", "#60a5fa", "#93c5fd", "#ec4899", "#8b5cf6"] }, // Deep blues and neon pinks
              links: {
                color: "#1e40af", // Deep blue lines
                distance: 120,
                enable: true,
                opacity: 0.4,
                width: 1.5,
              },
              move: {
                direction: "none",
                enable: true,
                outModes: { default: "out" }, // Drift away smoothly instead of bouncing
                random: true,
                speed: 0.5, // Slow, ambient movement
                straight: false,
              },
              number: {
                density: { enable: true, area: 800 },
                value: 150,
              },
              opacity: {
                value: 0.8,
                random: true,
                anim: { enable: true, speed: 1, opacity_min: 0.1, sync: false }
              },
              shape: { type: "circle" },
              size: {
                value: 3,
                random: true,
                anim: { enable: true, speed: 2, size_min: 0.5, sync: false }
              },
            },
            detectRetina: true,
          }}
      />
      <div className="app-container">
        <header className="app-header">
          <div className="logo">MFA</div>
        <div className="header-text">
          <h1>Mutual Fund Assistant</h1>
          <p className="disclaimer">Facts-only. No investment advice.</p>
        </div>
      </header>

      <main className="chat-container">
        <div className="messages-area">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message-wrapper ${msg.role}`}>
              <div className={`message-bubble ${msg.role} ${msg.isError ? 'error' : ''}`}>
                <div className="message-content" dangerouslySetInnerHTML={formatContent(msg.content)} />
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="message-wrapper assistant">
              <div className="message-bubble assistant typing">
                <div className="dot"></div>
                <div className="dot"></div>
                <div className="dot"></div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="bottom-section">
          {messages.length < 3 && (
            <div className="quick-actions">
              {quickActions.map((action, idx) => (
                <button key={idx} className="quick-action-btn" onClick={() => handleSend(action)}>
                  {action}
                </button>
              ))}
            </div>
          )}

          <div className="input-area">
            <input 
              type="text" 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSend(input)}
              placeholder="Ask a factual question..."
              disabled={isLoading}
            />
            <button className="send-btn" onClick={() => handleSend(input)} disabled={isLoading || !input.trim()}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </div>
        </div>
      </main>
    </div>
    </>
  );
}

export default App;
