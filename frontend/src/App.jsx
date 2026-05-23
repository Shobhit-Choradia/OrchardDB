import React, { useState, useEffect } from "react";
import { 
  Moon, Sun, FolderOpen, Plus, Lock, Trash2, 
  CloudUpload, Copy, RotateCw, Eye, EyeOff, X, 
  LogOut, CheckCircle2, AlertTriangle, Search, Database, ChevronRight 
} from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000/api";

export default function App() {
  // --- State Configuration ---
  const [theme, setTheme] = useState(localStorage.getItem("lunar_theme") || "dark");
  const [username, setUsername] = useState(localStorage.getItem("lunar_username") || null);
  const [apiKey, setApiKey] = useState(localStorage.getItem("lunar_api_key") || null);
  const [showKey, setShowKey] = useState(false);
  
  const [collections, setCollections] = useState([]);
  const [activeCollection, setActiveCollection] = useState(null);
  
  // UI Tabs & Toggles
  const [activeTab, setActiveTab] = useState("query");
  const [codeLang, setCodeLang] = useState("python");
  const [authModal, setAuthModal] = useState({ open: false, mode: "login" }); // login / register
  const [createColModal, setCreateColModal] = useState(false);
  const [toasts, setToasts] = useState([]);
  
  // Forms & Inputs
  const [authUsername, setAuthUsername] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [colName, setColName] = useState("");
  const [colMetric, setColMetric] = useState("cosine");
  
  // Search Sandbox
  const [queryText, setQueryText] = useState("");
  const [queryLimit, setQueryLimit] = useState(5);
  const [queryResults, setQueryResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // Index Document Sandbox
  const [docId, setDocId] = useState("");
  const [docText, setDocText] = useState("");
  const [docMeta, setDocMeta] = useState("");
  const [isIndexing, setIsIndexing] = useState(false);
  const [collectionDocs, setCollectionDocs] = useState([]);
  const [isLoadingDocs, setIsLoadingDocs] = useState(false);

  // --- Effects ---
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("lunar_theme", theme);
  }, [theme]);

  useEffect(() => {
    if (apiKey) {
      fetchCollections();
    }
  }, [apiKey]);

  useEffect(() => {
    if (activeCollection && activeTab === "documents") {
      fetchDocuments();
    }
  }, [activeCollection, activeTab]);

  // --- Toast Handler ---
  const triggerToast = (message, type = "success") => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3500);
  };

  // --- Core API Integrations ---
  const fetchCollections = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/vdb/collections`, {
        headers: { "x-api-key": apiKey }
      });
      const data = await res.json();
      if (res.ok) {
        setCollections(data.collections || []);
      } else {
        triggerToast(data.detail || "Error loading collections.", "error");
      }
    } catch {
      triggerToast("Failed to reach vector database service.", "error");
    }
  };

  const handleAuthSubmit = async (e) => {
    e.preventDefault();
    if (!authUsername.trim() || !authPassword) {
      triggerToast("Username and password are required.", "error");
      return;
    }

    const endpoint = authModal.mode === "login" ? "/auth/login" : "/auth/register";
    try {
      const res = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: authUsername.trim(), password: authPassword })
      });
      const data = await res.json();
      
      if (res.ok) {
        setUsername(authUsername.trim());
        setApiKey(data.api_key);
        localStorage.setItem("lunar_username", authUsername.trim());
        localStorage.setItem("lunar_api_key", data.api_key);
        setAuthModal({ open: false, mode: "login" });
        setAuthUsername("");
        setAuthPassword("");
        // Programmatically clear trailing hashes like #architecture
        window.history.pushState("", document.title, window.location.pathname + window.location.search);
        triggerToast(authModal.mode === "login" ? "Signed in successfully!" : "Account registered successfully!", "success");
      } else {
        triggerToast(data.detail || "Authentication failed.", "error");
      }
    } catch {
      triggerToast("Connection failed. Ensure backend API is active.", "error");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("lunar_username");
    localStorage.removeItem("lunar_api_key");
    setUsername(null);
    setApiKey(null);
    setCollections([]);
    setActiveCollection(null);
    setQueryResults([]);
    setCollectionDocs([]);
    // Programmatically clear trailing hashes like #architecture
    window.history.pushState("", document.title, window.location.pathname + window.location.search);
    triggerToast("Logged out successfully.", "success");
  };

  const handleCreateCollection = async (e) => {
    e.preventDefault();
    const formattedName = colName.trim().replace(/\s+/g, "-");
    if (!formattedName) return;

    try {
      const res = await fetch(`${API_BASE_URL}/vdb/collections`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey
        },
        body: JSON.stringify({ name: formattedName, metric: colMetric })
      });
      const data = await res.json();
      
      if (res.ok) {
        setColName("");
        setCreateColModal(false);
        triggerToast(`Collection '${formattedName}' created!`, "success");
        await fetchCollections();
        setActiveCollection(formattedName);
        setActiveTab("query");
      } else {
        triggerToast(data.detail || "Failed to create collection.", "error");
      }
    } catch {
      triggerToast("Error communicating with creation API.", "error");
    }
  };

  const handleDeleteCollection = async () => {
    if (!activeCollection) return;
    const confirmDelete = window.confirm(`Permanently delete collection '${activeCollection}' and all its vectors?`);
    if (!confirmDelete) return;

    try {
      const res = await fetch(`${API_BASE_URL}/vdb/collections/${activeCollection}`, {
        method: "DELETE",
        headers: { "x-api-key": apiKey }
      });
      
      if (res.ok) {
        triggerToast(`Collection '${activeCollection}' deleted.`, "success");
        setActiveCollection(null);
        fetchCollections();
      } else {
        const data = await res.json();
        triggerToast(data.detail || "Error deleting collection.", "error");
      }
    } catch {
      triggerToast("Server write error.", "error");
    }
  };

  const executeSearch = async () => {
    if (!queryText.trim()) {
      triggerToast("Please enter a similarity search query.", "error");
      return;
    }

    setIsSearching(true);
    try {
      const res = await fetch(`${API_BASE_URL}/vdb/collections/${activeCollection}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey
        },
        body: JSON.stringify({
          query_text: queryText.trim(),
          n_results: parseInt(queryLimit)
        })
      });
      const data = await res.json();
      setIsSearching(false);
      
      if (res.ok) {
        setQueryResults(data.results || []);
      } else {
        triggerToast(data.detail || "Search index query failed.", "error");
      }
    } catch {
      setIsSearching(false);
      triggerToast("Error executing query search.", "error");
    }
  };

  const fetchDocuments = async () => {
    setIsLoadingDocs(true);
    try {
      const res = await fetch(`${API_BASE_URL}/vdb/collections/${activeCollection}/documents`, {
        headers: { "x-api-key": apiKey }
      });
      const data = await res.json();
      setIsLoadingDocs(false);
      
      if (res.ok) {
        const ids = data.ids || [];
        const docs = data.documents || [];
        const metas = data.metadatas || [];
        const list = ids.map((id, index) => ({
          id,
          document: docs[index] || "",
          metadata: metas[index] || {}
        }));
        setCollectionDocs(list);
      } else {
        triggerToast("Failed to fetch current documents.", "error");
      }
    } catch {
      setIsLoadingDocs(false);
      triggerToast("Network communication error.", "error");
    }
  };

  const indexNewDocument = async () => {
    if (!docId.trim() || !docText.trim()) {
      triggerToast("Document ID and body text are required.", "error");
      return;
    }

    let metadatas = null;
    if (docMeta.trim()) {
      try {
        metadatas = [JSON.parse(docMeta.trim())];
      } catch {
        triggerToast("Metadata must be valid key-value JSON format.", "error");
        return;
      }
    }

    setIsIndexing(true);
    try {
      const res = await fetch(`${API_BASE_URL}/vdb/collections/${activeCollection}/documents`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey
        },
        body: JSON.stringify({
          ids: [docId.trim()],
          documents: [docText.trim()],
          metadatas: metadatas
        })
      });
      const data = await res.json();
      setIsIndexing(false);
      
      if (res.ok) {
        triggerToast("Document indexed successfully!", "success");
        setDocId("");
        setDocText("");
        setDocMeta("");
        fetchDocuments();
      } else {
        triggerToast(data.detail || "Error indexing document.", "error");
      }
    } catch {
      setIsIndexing(false);
      triggerToast("Network write error.", "error");
    }
  };

  const deleteSingleDoc = async (idToDelete) => {
    const confirmDocDel = window.confirm(`Delete document '${idToDelete}'?`);
    if (!confirmDocDel) return;

    try {
      const res = await fetch(`${API_BASE_URL}/vdb/collections/${activeCollection}/documents`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": apiKey
        },
        body: JSON.stringify({ ids: [idToDelete] })
      });
      
      if (res.ok) {
        triggerToast("Document removed.", "success");
        fetchDocuments();
      } else {
        const data = await res.json();
        triggerToast(data.detail || "Failed to delete document.", "error");
      }
    } catch {
      triggerToast("Server response failure.", "error");
    }
  };

  // --- Dynamic Code Snippets Block ---
  const generateSnippet = () => {
    const key = apiKey || "your_lunar_api_key";
    const col = activeCollection || "collection_name";
    if (codeLang === "python") {
      return `import requests

# Vector client details
BASE_URL = "http://127.0.0.1:8000/api/vdb"
HEADERS = {
    "X-API-Key": "${key}",
    "Content-Type": "application/json"
}

# 1. Index context data
payload_upsert = {
    "ids": ["item_1"],
    "documents": ["LunarDB wraps ChromaDB securely, providing robust trials."],
    "metadatas": [{"category": "demo"}]
}
requests.post(f"{BASE_URL}/collections/${col}/documents", headers=HEADERS, json=payload_upsert)

# 2. Perform similarity search query
payload_query = {
    "query_text": "What is LunarDB?",
    "n_results": 2
}
response = requests.post(f"{BASE_URL}/collections/${col}/query", headers=HEADERS, json=payload_query)
print(response.json())`;
    } else {
      return `// JavaScript Fetch SDK Integration
const baseUrl = "http://127.0.0.1:8000/api/vdb";
const headers = {
  "X-API-Key": "${key}",
  "Content-Type": "application/json"
};

// 1. Index document into collection namespace
fetch(\`\${baseUrl}/collections/${col}/documents\`, {
  method: "POST",
  headers: headers,
  body: JSON.stringify({
    ids: ["item_1"],
    documents: ["LunarDB is modern and developer-first."],
    metadatas: [{ category: "demo" }]
  })
})
.then(res => res.json())
.then(data => console.log("Indexed successfully:", data));

// 2. Query similarity matches
fetch(\`\${baseUrl}/collections/${col}/query\`, {
  method: "POST",
  headers: headers,
  body: JSON.stringify({
    query_text: "What is LunarDB?",
    n_results: 2
  })
})
.then(res => res.json())
.then(matches => console.log("Similarity Search Nearest Neighbors:", matches));`;
    }
  };

  const copyToClipboard = (text, toastMsg) => {
    navigator.clipboard.writeText(text);
    triggerToast(toastMsg, "success");
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header Panel */}
      <header className="main-header">
        <div className="header-container">
          <div className="logo" onClick={() => setActiveCollection(null)}>
            <Database className="glow-icon" />
            <span className="logo-text">Lunar<span className="logo-accent">DB</span></span>
            <span className="badge">Trial v1.0</span>
          </div>

          {apiKey ? (
            <nav className="nav-links">
              <button className="nav-link-btn" onClick={() => { setActiveCollection(null); setActiveTab("query"); }}>
                Workspace Console
              </button>
            </nav>
          ) : (
            <nav className="nav-links">
              <a href="#features">Features</a>
              <a href="#architecture">Architecture</a>
              <button className="nav-btn-console btn btn-sm btn-secondary" onClick={() => setAuthModal({ open: true, mode: "login" })}>
                Enter Console
              </button>
            </nav>
          )}

          <div className="header-controls">
            <button 
              onClick={() => setTheme(prev => prev === "dark" ? "light" : "dark")} 
              className="icon-btn" 
              title="Toggle Light/Dark Theme"
            >
              {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            
            {apiKey && username && (
              <div id="user-status-container">
                <span id="header-username">{username}</span>
                <button onClick={handleLogout} className="btn btn-outline btn-sm" title="Sign Out">
                  <LogOut size={14} />
                  <span>Log out</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Viewport */}
      <main className="content-container">
        
        {/* LANDING MARKETING HERO (Visible when logged out) */}
        {!apiKey && (
          <section className="landing-section">
            <div className="hero-content">
              <h1 className="hero-title">
                Vector DB as a Service, <br />
                <span className="gradient-text">Simplified for Speed.</span>
              </h1>
              <p className="hero-subtitle">
                LunarDB wraps ChromaDB with seamless multi-tenancy, instant API key authorization, and a stunning developer console. Start trial indexing in seconds.
              </p>
              
              <div className="hero-actions">
                <button className="btn btn-primary btn-lg" onClick={() => setAuthModal({ open: true, mode: "register" })}>
                  Start Trial Free
                </button>
                <button className="btn btn-secondary btn-lg" onClick={() => setAuthModal({ open: true, mode: "login" })}>
                  Sign In to Console
                </button>
              </div>
            </div>

            <div className="hero-preview">
              <div className="preview-browser">
                <div className="browser-bar">
                  <span className="dot red"></span>
                  <span className="dot yellow"></span>
                  <span className="dot green"></span>
                  <span className="browser-title">console.lunardb.dev</span>
                </div>
                <div className="preview-content">
                  <div className="preview-sidebar"></div>
                  <div className="preview-main">
                    <div className="preview-card"></div>
                    <div className="preview-card"></div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* DEVELOPER DASHBOARD CONSOLE (Visible when logged in) */}
        {apiKey && (
          <section className="console-section">
            <div className="console-grid">
              
              {/* Credentials Header Panel */}
              <div className="full-width-card welcome-card">
                <div className="welcome-left">
                  <h2>Welcome back, <span className="highlight-text">{username}</span>!</h2>
                  <p>Your isolated vector database namespace is secured and active.</p>
                </div>
                <div className="api-key-panel">
                  <span className="panel-label">Active Secret SDK API Key:</span>
                  <div className="api-key-wrapper">
                    <input 
                      type={showKey ? "text" : "password"} 
                      value={apiKey} 
                      readOnly 
                    />
                    <button className="icon-btn" onClick={() => copyToClipboard(apiKey, "API Key copied!")} title="Copy Key">
                      <Copy size={16} />
                    </button>
                    <button className="icon-btn" onClick={() => setShowKey(prev => !prev)} title={showKey ? "Hide key" : "Show key"}>
                      {showKey ? <EyeOff size={16} /> : <Eye size={16} />}
                    </button>
                  </div>
                </div>
              </div>

              {/* Grid Column 1: Collections Browser */}
              <div className="console-col">
                <div className="console-card">
                  <div className="card-header">
                    <h3>
                      <FolderOpen />
                      <span>Vector Collections</span>
                    </h3>
                    <button className="btn btn-sm btn-primary" onClick={() => setCreateColModal(true)}>
                      <Plus size={14} />
                      <span>New</span>
                    </button>
                  </div>

                  <div className="card-body">
                    {collections.length === 0 ? (
                      <div className="empty-state">
                        <FolderOpen />
                        <p>No collections initialized yet.</p>
                        <button className="btn btn-sm btn-outline" onClick={() => setCreateColModal(true)}>
                          Create First Space
                        </button>
                      </div>
                    ) : (
                      <ul className="collections-list">
                        {collections.map(col => (
                          <li 
                            key={col}
                            onClick={() => {
                              setActiveCollection(col);
                              setQueryResults([]);
                              setCollectionDocs([]);
                              setActiveTab("query");
                            }}
                            className={`collection-item ${activeCollection === col ? "active" : ""}`}
                          >
                            <div className="col-info">
                              <span className="col-name">{col}</span>
                              <span className="col-metric">Metric: Cosine</span>
                            </div>
                            <ChevronRight size={16} className="text-muted" />
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                </div>
              </div>

              {/* Grid Column 2: Vector Sandbox Playground */}
              <div className="console-col">
                <div className="console-card">
                  
                  {!activeCollection ? (
                    <div className="empty-state sandbox-locked">
                      <Lock />
                      <h4>Interactive Sandbox Locked</h4>
                      <p>Select or create a collection from the left sidebar to unlock the vector playground.</p>
                    </div>
                  ) : (
                    <div>
                      {/* Active Collection Header */}
                      <div className="card-header border-bottom">
                        <div className="sandbox-title-area">
                          <h3>{activeCollection}</h3>
                          <span className="metric-badge">cosine</span>
                        </div>
                        <button onClick={handleDeleteCollection} className="btn btn-sm btn-danger">
                          <Trash2 size={14} />
                          <span>Delete Collection</span>
                        </button>
                      </div>

                      {/* Playground Tabs */}
                      <div className="sandbox-tabs">
                        <button 
                          className={`tab-btn ${activeTab === "query" ? "active" : ""}`}
                          onClick={() => setActiveTab("query")}
                        >
                          Semantic Search Sandbox
                        </button>
                        <button 
                          className={`tab-btn ${activeTab === "documents" ? "active" : ""}`}
                          onClick={() => {
                            setActiveTab("documents");
                            fetchDocuments();
                          }}
                        >
                          Index Documents Table
                        </button>
                        <button 
                          className={`tab-btn ${activeTab === "code" ? "active" : ""}`}
                          onClick={() => setActiveTab("code")}
                        >
                          Developer SDK Integration
                        </button>
                      </div>

                      {/* Tab Content 1: Semantic Query */}
                      {activeTab === "query" && (
                        <div className="tab-content">
                          <div className="query-sandbox-form">
                            <div className="input-group">
                              <input 
                                type="text" 
                                value={queryText}
                                onChange={(e) => setQueryText(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && executeSearch()}
                                placeholder="Enter natural language query phrase (e.g. 'what is a vector db?')..." 
                              />
                              <button onClick={executeSearch} className="btn btn-primary" disabled={isSearching}>
                                {isSearching ? <RotateCw className="animate-spin" size={16} /> : <Search size={16} />}
                                <span>{isSearching ? "Searching..." : "Search"}</span>
                              </button>
                            </div>
                            
                            <div className="query-options">
                              <label htmlFor="limit-select">Limit results (K):</label>
                              <select 
                                id="limit-select" 
                                value={queryLimit}
                                onChange={(e) => setQueryLimit(e.target.value)}
                              >
                                <option value={3}>3 matches</option>
                                <option value={5}>5 matches</option>
                                <option value={10}>10 matches</option>
                              </select>
                            </div>
                          </div>

                          <div className="query-results-wrapper">
                            <h4>Search Results</h4>
                            {queryResults.length === 0 ? (
                              <div className="results-empty">
                                <Database />
                                <p>Submit a search query above to view semantic nearest neighbors in index database.</p>
                              </div>
                            ) : (
                              <div className="results-list">
                                {queryResults.map(match => (
                                  <div key={match.id} className="match-card">
                                    <div className="match-header">
                                      <span className="match-id">{match.id}</span>
                                      <span className="match-distance highlight-text">
                                        Distance Score: {match.distance !== null ? match.distance.toFixed(4) : "N/A"}
                                      </span>
                                    </div>
                                    <div className="match-body">{match.document}</div>
                                    {match.metadata && Object.keys(match.metadata).length > 0 && (
                                      <div className="match-meta">
                                        Metadata: {JSON.stringify(match.metadata)}
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Tab Content 2: Document Index Management */}
                      {activeTab === "documents" && (
                        <div className="tab-content">
                          <div className="form-container">
                            <h4>Add New Document to Vector Space</h4>
                            <p className="section-desc">ChromaDB automatically computes text embeddings using its default lightweight Sentence-Transformers pipeline.</p>
                            
                            <div className="form-group">
                              <label>Unique Document ID</label>
                              <input 
                                type="text" 
                                value={docId}
                                onChange={(e) => setDocId(e.target.value)}
                                placeholder="e.g. doc_101" 
                              />
                            </div>
                            <div className="form-group">
                              <label>Document Body Text</label>
                              <textarea 
                                rows={3}
                                value={docText}
                                onChange={(e) => setDocText(e.target.value)}
                                placeholder="Enter content you want to store and search against..."
                              ></textarea>
                            </div>
                            <div className="form-group">
                              <label>Metadata Attributes JSON (Optional)</label>
                              <input 
                                type="text" 
                                value={docMeta}
                                onChange={(e) => setDocMeta(e.target.value)}
                                placeholder='e.g. {"category": "AI", "tags": ["search"]}' 
                              />
                            </div>
                            <button className="btn btn-primary" onClick={indexNewDocument} disabled={isIndexing}>
                              <CloudUpload size={16} />
                              <span>{isIndexing ? "Indexing..." : "Index Document"}</span>
                            </button>
                          </div>

                          <hr className="card-divider" />

                          <div className="indexed-documents-table-wrapper">
                            <div className="table-header">
                              <h4>Current Indexed Records</h4>
                              <button onClick={fetchDocuments} className="icon-btn" title="Refresh list" disabled={isLoadingDocs}>
                                <RotateCw className={isLoadingDocs ? "animate-spin" : ""} size={16} />
                              </button>
                            </div>
                            
                            <div className="table-scroll">
                              <table className="documents-table">
                                <thead>
                                  <tr>
                                    <th>ID</th>
                                    <th>Document Text Preview</th>
                                    <th>Metadata</th>
                                    <th>Action</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {collectionDocs.length === 0 ? (
                                    <tr>
                                      <td colSpan={4} style={{ textAlign: "center", color: "var(--text-muted)", padding: "2rem" }}>
                                        No documents currently stored in this namespace.
                                      </td>
                                    </tr>
                                  ) : (
                                    collectionDocs.map(doc => (
                                      <tr key={doc.id}>
                                        <td style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{doc.id}</td>
                                        <td>{doc.document}</td>
                                        <td className="doc-meta-badge">{JSON.stringify(doc.metadata)}</td>
                                        <td>
                                          <button 
                                            onClick={() => deleteSingleDoc(doc.id)} 
                                            className="icon-btn" 
                                            style={{ color: "var(--danger-color)" }}
                                            title="Delete document"
                                          >
                                            <Trash2 size={14} />
                                          </button>
                                        </td>
                                      </tr>
                                    ))
                                  )}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* Tab Content 3: SDK Developer Code Integration */}
                      {activeTab === "code" && (
                        <div className="tab-content">
                          <div className="code-tab-header">
                            <h4>SDK & HTTP Integration Boilerplate</h4>
                            <p className="section-desc">Instantly query or populate this collection securely from your applications using your API Key.</p>
                          </div>
                          
                          <div className="snippet-selector">
                            <button 
                              className={`snippet-tab-btn ${codeLang === "python" ? "active" : ""}`}
                              onClick={() => setCodeLang("python")}
                            >
                              Python (requests)
                            </button>
                            <button 
                              className={`snippet-tab-btn ${codeLang === "js" ? "active" : ""}`}
                              onClick={() => setCodeLang("js")}
                            >
                              JavaScript (fetch)
                            </button>
                          </div>

                          <div className="code-preview-container">
                            <pre>
                              <code>{generateSnippet()}</code>
                            </pre>
                            <button 
                              onClick={() => copyToClipboard(generateSnippet(), "Code snippet copied!")} 
                              className="btn btn-sm btn-outline" 
                              id="copy-snippet-btn"
                            >
                              <Copy size={12} />
                              <span>Copy Code</span>
                            </button>
                          </div>
                        </div>
                      )}

                    </div>
                  )}

                </div>
              </div>

            </div>
          </section>
        )}

      </main>

      <footer className="main-footer">
        <p>&copy; 2026 LunarDB. Built for lightweight vector database trials. Powered by ChromaDB.</p>
      </footer>

      {/* MODAL 1: AUTHENTICATION (Register / Login) */}
      {authModal.open && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3>{authModal.mode === "login" ? "Sign In to Console" : "Create Trial Account"}</h3>
              <button className="icon-btn" onClick={() => setAuthModal({ open: false, mode: "login" })}>
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              <form onSubmit={handleAuthSubmit}>
                <div className="form-group">
                  <label>Username</label>
                  <input 
                    type="text" 
                    required 
                    value={authUsername}
                    onChange={(e) => setAuthUsername(e.target.value)}
                    placeholder="e.g. dev_lunar" 
                  />
                </div>
                <div className="form-group">
                  <label>Password</label>
                  <input 
                    type="password" 
                    required 
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    placeholder="••••••••" 
                  />
                </div>
                <div className="form-footer">
                  <button type="submit" className="btn btn-primary">
                    {authModal.mode === "login" ? "Login" : "Register & Get Key"}
                  </button>
                  <button type="button" className="btn btn-outline" onClick={() => setAuthModal({ open: false, mode: "login" })}>
                    Cancel
                  </button>
                </div>
              </form>
              <div className="auth-toggle-prompt">
                <span>{authModal.mode === "login" ? "Don't have an account?" : "Already have an account?"}</span>{" "}
                <a 
                  href="#" 
                  onClick={(e) => {
                    e.preventDefault();
                    setAuthModal(prev => ({ ...prev, mode: prev.mode === "login" ? "register" : "login" }));
                  }}
                >
                  {authModal.mode === "login" ? "Create one now" : "Login here"}
                </a>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* MODAL 2: CREATE COLLECTION */}
      {createColModal && (
        <div className="modal-overlay">
          <div className="modal-card">
            <div className="modal-header">
              <h3>Initialize Vector Collection</h3>
              <button className="icon-btn" onClick={() => setCreateColModal(false)}>
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              <form onSubmit={handleCreateCollection}>
                <div className="form-group">
                  <label>Collection Name</label>
                  <input 
                    type="text" 
                    required 
                    value={colName}
                    onChange={(e) => setColName(e.target.value)}
                    placeholder="e.g. customer-kb" 
                  />
                </div>
                <div className="form-group">
                  <label>Distance Similarity Metric</label>
                  <select 
                    value={colMetric}
                    onChange={(e) => setColMetric(e.target.value)}
                  >
                    <option value="cosine">Cosine Distance (Recommended)</option>
                    <option value="l2">L2 / Euclidean Distance</option>
                    <option value="ip">Inner Product (Dot Product)</option>
                  </select>
                </div>
                <div className="form-footer">
                  <button type="submit" className="btn btn-primary">Initialize Collection</button>
                  <button type="button" className="btn btn-outline" onClick={() => setCreateColModal(false)}>
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* TOAST SYSTEM */}
      <div className="toast-container">
        {toasts.map(toast => (
          <div key={toast.id} className={`toast ${toast.type}`}>
            {toast.type === "success" ? <CheckCircle2 /> : <AlertTriangle />}
            <span>{toast.message}</span>
          </div>
        ))}
      </div>

    </div>
  );
}
