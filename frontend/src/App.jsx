import { useMemo, useState } from "react";
import "./App.css";

function App() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle");
  const [error, setError] = useState("");
  const [decisions, setDecisions] = useState([]);
  const [actionItems, setActionItems] = useState([]);
  const [rawResponse, setRawResponse] = useState("");
  const [meetingId, setMeetingId] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [chatQuestion, setChatQuestion] = useState("");
  const [chatStatus, setChatStatus] = useState("idle");
  const [chatError, setChatError] = useState("");
  const [minutesText, setMinutesText] = useState("");
  const [minutesStatus, setMinutesStatus] = useState("idle");
  const [minutesError, setMinutesError] = useState("");
  const apiBase = import.meta.env.VITE_API_BASE_URL || "";
  const endpoint = `${apiBase}/api/parse`;
  const chatEndpoint = `${apiBase}/api/ask`;
  const minutesEndpoint = `${apiBase}/api/minutes`;

  const fileLabel = useMemo(() => {
    if (!file) return "Drop a .txt or .vtt file here";
    return `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
  }, [file]);

  const renderMessage = (content) => {
    const segments = content.split(/(\*\*[^*]+\*\*)/g);
    return segments.map((segment, index) => {
      if (segment.startsWith("**") && segment.endsWith("**")) {
        return <strong key={`bold-${index}`}>{segment.slice(2, -2)}</strong>;
      }

      const lines = segment.split("\n");
      return lines.map((line, lineIndex) => (
        <span key={`text-${index}-${lineIndex}`}>
          {line}
          {lineIndex < lines.length - 1 ? <br /> : null}
        </span>
      ));
    });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file || status === "loading") return;

    const payload = new FormData();
    payload.append("file", file);

    setStatus("loading");
    setError("");
    setDecisions([]);
    setActionItems([]);
    setRawResponse("");
    setMeetingId("");
    setMinutesText("");
    setMinutesStatus("idle");
    setMinutesError("");

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        body: payload,
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Request failed (${response.status})`);
      }

      const contentType = response.headers.get("content-type") || "";
      if (contentType.includes("application/json")) {
        const data = await response.json();
        const entries = Array.isArray(data) ? data : data.entries || [];
        setMeetingId(data.meeting_id || "");
        const decisionsOnly = entries.filter(
          (entry) => entry.type === "decision",
        );
        const actionItemsOnly = entries.filter(
          (entry) => entry.type === "action_item",
        );
        setDecisions(decisionsOnly);
        setActionItems(actionItemsOnly);
        setRawResponse(JSON.stringify(entries, null, 2));
      } else {
        const text = await response.text();
        setRawResponse(text);
      }

      setStatus("success");
    } catch (caught) {
      setError(caught?.message || "Upload failed. Please try again.");
      setStatus("error");
    }
  };

  const handleGenerateMinutes = async () => {
    if (!meetingId || minutesStatus === "loading") return;

    setMinutesStatus("loading");
    setMinutesError("");

    try {
      const response = await fetch(minutesEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ meeting_id: meetingId }),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Request failed (${response.status})`);
      }

      const data = await response.json();
      setMinutesText(data.minutes || "No minutes returned.");
      setMinutesStatus("success");
    } catch (caught) {
      setMinutesError(
        caught?.message || "Minutes generation failed. Please try again.",
      );
      setMinutesStatus("error");
    }
  };

  const handleAsk = async (event) => {
    event.preventDefault();
    if (!chatQuestion.trim() || chatStatus === "loading") return;

    const question = chatQuestion.trim();
    setChatQuestion("");
    setChatStatus("loading");
    setChatError("");

    setChatMessages((prev) => [...prev, { role: "user", content: question }]);

    try {
      const response = await fetch(chatEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        const message = await response.text();
        throw new Error(message || `Request failed (${response.status})`);
      }

      const data = await response.json();
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer || "No answer returned." },
      ]);
      setChatStatus("success");
    } catch (caught) {
      setChatError(caught?.message || "Chat request failed. Please try again.");
      setChatStatus("error");
    }
  };

  return (
    <main className="page">
      <header className="hero">
        <div className="hero-badge">ClarityMeet</div>
        <h1>Upload transcripts. Extract decisions.</h1>
        <p>
          Drop a meeting transcript and receive a clean list of decisions from
          the backend in seconds.
        </p>
      </header>

      <section className="panel">
        <form className="upload" onSubmit={handleSubmit}>
          <label className="drop" htmlFor="file">
            <input
              id="file"
              name="file"
              type="file"
              accept=".txt,.vtt"
              onChange={(event) => setFile(event.target.files?.[0] || null)}
            />
            <span className="drop-title">{fileLabel}</span>
            <span className="drop-subtitle">
              Accepted: .txt or .vtt (max 25 MB)
            </span>
          </label>

          <div className="controls">
            <button className="primary" type="submit" disabled={!file}>
              {status === "loading" ? "Uploading..." : "Analyze transcript"}
            </button>
          </div>
        </form>

        {meetingId ? (
          <div className="notice info">Meeting ID: {meetingId}</div>
        ) : null}

        <div className="controls minutes-actions">
          <button
            className="primary"
            type="button"
            onClick={handleGenerateMinutes}
            disabled={!meetingId || minutesStatus === "loading"}
          >
            {minutesStatus === "loading" ? "Generating..." : "Generate minutes"}
          </button>
        </div>

        {minutesError ? (
          <div className="notice error">{minutesError}</div>
        ) : null}

        {error ? <div className="notice error">{error}</div> : null}
        {status === "success" &&
        decisions.length === 0 &&
        actionItems.length === 0 &&
        rawResponse ? (
          <div className="notice info">Response received.</div>
        ) : null}
      </section>

      {minutesText ? (
        <section className="panel minutes-panel">
          <div className="results-header">
            <h2>Meeting minutes</h2>
            <span className="meta">Generated from the latest upload</span>
          </div>
          <div className="minutes-content">{renderMessage(minutesText)}</div>
        </section>
      ) : null}

      <section className="panel chat">
        <div className="results-header">
          <h2>Meeting intelligence</h2>
          <span className="meta">Ask across stored meetings</span>
        </div>

        <div className="chat-window">
          {chatMessages.length ? (
            chatMessages.map((message, index) => (
              <div
                className={`chat-bubble ${message.role}`}
                key={`${message.role}-${index}`}
              >
                <span className="chat-role">
                  {message.role === "user" ? "You" : "ClarityMeet"}
                </span>
                <p>{renderMessage(message.content)}</p>
              </div>
            ))
          ) : (
            <div className="empty">
              Ask about decisions, owners, or rationale.
            </div>
          )}
        </div>

        <form className="chat-form" onSubmit={handleAsk}>
          <input
            className="chat-input"
            type="text"
            value={chatQuestion}
            onChange={(event) => setChatQuestion(event.target.value)}
            placeholder="What decisions did we make about shipping?"
          />
          <button className="primary" type="submit">
            {chatStatus === "loading" ? "Thinking..." : "Ask"}
          </button>
        </form>

        {chatError ? <div className="notice error">{chatError}</div> : null}
      </section>

      <section className="results">
        <div className="results-section">
          <div className="results-header">
            <h2>Decisions</h2>
            <span className="meta">
              {decisions.length
                ? `${decisions.length} found`
                : "Waiting on input"}
            </span>
          </div>

          <div className="results-grid">
            {decisions.length ? (
              decisions.map((decision, index) => (
                <article
                  className="card"
                  key={`${decision.timestamp}-${index}`}
                >
                  <h3>{decision.decision || `Decision ${index + 1}`}</h3>
                  <p className="detail">
                    {decision.timestamp} · {decision.speaker}
                  </p>
                </article>
              ))
            ) : (
              <div className="empty">No decisions yet.</div>
            )}
          </div>
        </div>

        <div className="results-section">
          <div className="results-header">
            <h2>Action Items</h2>
            <span className="meta">
              {actionItems.length
                ? `${actionItems.length} found`
                : "Waiting on input"}
            </span>
          </div>

          <div className="results-grid">
            {actionItems.length ? (
              actionItems.map((item, index) => (
                <article className="card" key={`${item.timestamp}-${index}`}>
                  <h3>{item.action_item || `Action Item ${index + 1}`}</h3>
                  <p className="detail">
                    {item.timestamp} · {item.speaker}
                  </p>
                  {item.who ? (
                    <p className="detail">Owner: {item.who}</p>
                  ) : null}
                  {item.when ? (
                    <p className="detail">Due: {item.when}</p>
                  ) : null}
                </article>
              ))
            ) : (
              <div className="empty">No action items yet.</div>
            )}
          </div>
        </div>

        {rawResponse ? (
          <div className="raw">
            <div className="raw-header">Raw response</div>
            <pre>{rawResponse}</pre>
          </div>
        ) : null}
      </section>
    </main>
  );
}

export default App;
