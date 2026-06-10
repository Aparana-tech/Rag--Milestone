import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import Particles, { initParticlesEngine } from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";
import './index.css';

function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your AI Assistant. I can provide facts about HDFC Mutual Funds.', type: 'greeting' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [init, setInit] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    initParticlesEngine(async (engine) => {
      await loadSlim(engine);
    }).then(() => {
      setInit(true);
    });
  }, []);

  const quickActions = [
    "What is the exit load for HDFC Defence Fund?",
    "List the top holdings of HDFC Gold ETF.",
    "Tell me the AUM of HDFC Sensex Index Fund."
  ];

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
      {init && (
        <Particles
          id="tsparticles"
          options={{
            background: {
              color: { value: "transparent" },
            },
            fpsLimit: 60,
            interactivity: {
              events: {
                onClick: { enable: true, mode: "push" },
                onHover: { enable: true, mode: "grab" },
                resize: true,
              },
              modes: {
                push: { quantity: 4 },
                grab: { distance: 150, links: { opacity: 0.5 } },
              },
            },
            particles: {
              color: { value: ["#3b82f6", "#8b5cf6", "#ec4899", "#06b6d4"] },
              links: {
                color: "#3b82f6",
                distance: 150,
                enable: true,
                opacity: 0.2,
                width: 1,
              },
              move: {
                direction: "none",
                enable: true,
                outModes: { default: "bounce" },
                random: false,
                speed: 1,
                straight: false,
              },
              number: {
                density: { enable: true, area: 800 },
                value: 80,
              },
              opacity: {
                value: 0.6,
                animation: { enable: true, speed: 1, minimumValue: 0.1 }
              },
              shape: { type: "circle" },
              size: {
                value: { min: 1, max: 4 },
                animation: { enable: true, speed: 2, minimumValue: 0.5 }
              },
            },
            detectRetina: true,
          }}
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            zIndex: -1,
          }}
        />
      )}
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
