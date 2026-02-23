import { FormEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from 'react';
import { askResume } from './api';
import type { ChatMessage } from './types';

const starterPrompts = [
  'What kind of backend work has Sunay done?',
  'Summarize Sunay\'s AI experience in 3 bullets.',
  'Which technologies are strongest in this profile?',
];

function App() {
  const initialAssistantMessage: ChatMessage = {
    role: 'assistant',
    content:
      'Welcome. I can answer about Sunay\'s projects, skills, education, growth story, and career direction.',
  };

  const [messages, setMessages] = useState<ChatMessage[]>([
    initialAssistantMessage,
  ]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  const canSubmit = question.trim().length > 1 && !loading;

  useEffect(() => {
    const chatLog = logRef.current;
    if (!chatLog) return;
    chatLog.scrollTop = chatLog.scrollHeight;
  }, [messages, loading]);

  const stats = useMemo(
    () => [
      { label: 'Builder Focus', value: 'Product + AI + Full-stack' },
      { label: 'Core Strength', value: 'DSA + Deployable Projects' },
      { label: 'Current Goal', value: 'Internship + Startup readiness' },
    ],
    []
  );

  async function handleAsk(input: string) {
    const text = input.trim();
    if (text.length < 2) return;

    setError(null);
    setLoading(true);
    setMessages((prev) => [...prev, { role: 'user', content: text }]);
    setQuestion('');

    try {
      const result = await askResume(text);
      setMessages((prev) => [...prev, { role: 'assistant', content: result.answer }]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            'I could not reach the chat backend. Verify backend server and OpenRouter key setup.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await handleAsk(question);
  }

  function onInputKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      if (canSubmit) {
        void handleAsk(question);
      }
    }
  }

  function resetConversation() {
    setMessages([initialAssistantMessage]);
    setQuestion('');
    setError(null);
  }

  return (
    <div className="page">
      <div className="mesh mesh-a" />
      <div className="mesh mesh-b" />

      <header className="topbar">
        <p className="eyebrow">Portfolio AI</p>
        <h1>Sunay Revad</h1>
      </header>

      <main className="layout">
        <section className="identity panel">
          <p className="identity-tag">About Sunay</p>
          <h2>
            Curious builder with
            <span> startup-driven execution.</span>
          </h2>
          <p className="identity-copy">
            DAIICT ICT student focused on full-stack product building, strong DSA practice, and AI-driven
            application thinking.
          </p>

          <div className="stats">
            {stats.map((item) => (
              <article key={item.label} className="stat-card">
                <p>{item.label}</p>
                <h3>{item.value}</h3>
              </article>
            ))}
          </div>

          <div className="highlights">
            <h3>Highlights</h3>
            <ul>
              <li>Built and deployed AI Finance Platform and Blog Platform.</li>
              <li>Combines practical project building with disciplined DSA preparation.</li>
              <li>Strong interest in personalization systems and AI startup ideas.</li>
            </ul>
          </div>

          <div className="link-grid">
            <a href="https://github.com/Sunay4826" target="_blank" rel="noreferrer">
              GitHub
            </a>
            <a href="https://ai-finance-platform-3qj9.vercel.app" target="_blank" rel="noreferrer">
              AI Finance
            </a>
            <a href="https://blog-sbyr.vercel.app/signin" target="_blank" rel="noreferrer">
              Blog Platform
            </a>
          </div>
        </section>

        <section className="chat panel">
          <div className="chat-topbar">
            <div>
              <h2>Ask Resume Copilot</h2>
              <p>{loading ? 'Generating response...' : 'Realtime answers from portfolio knowledge'}</p>
            </div>
            <div className="chat-meta">
              <span className={`status ${loading ? 'busy' : 'live'}`}>{loading ? 'Busy' : 'Live'}</span>
              <button type="button" className="reset-btn" onClick={resetConversation} disabled={loading}>
                Reset
              </button>
            </div>
          </div>

          <div className="prompt-row">
            {starterPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="prompt-btn"
                disabled={loading}
                onClick={() => handleAsk(prompt)}
              >
                {prompt}
              </button>
            ))}
          </div>

          <div className="chat-log" ref={logRef} role="log" aria-live="polite">
            {messages.map((message, index) => (
              <article key={`${message.role}-${index}`} className={`message ${message.role}`}>
                <span className="role-label">{message.role === 'user' ? 'You' : 'Assistant'}</span>
                <p>{message.content}</p>
              </article>
            ))}
            {loading ? (
              <article className="message assistant typing" aria-label="Assistant is typing">
                <span className="role-label">Assistant</span>
                <div className="typing-dots">
                  <span />
                  <span />
                  <span />
                </div>
              </article>
            ) : null}
          </div>

          <form className="composer" onSubmit={onSubmit}>
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={onInputKeyDown}
              placeholder="Ask about skills, projects, stack, or experience..."
              aria-label="Question for resume assistant"
              rows={2}
            />
            <button type="submit" disabled={!canSubmit} className="send-btn">
              Send
            </button>
          </form>
          {error ? <p className="error-text">{error}</p> : null}
        </section>
      </main>
    </div>
  );
}

export default App;
