import React, { useState, useEffect } from "react";
import { 
  Moon, Sun, FolderOpen, Plus, Lock, Trash2, 
  CloudUpload, Copy, RotateCw, Eye, EyeOff, X, 
  LogOut, CheckCircle2, AlertTriangle, Search, Database, ChevronRight,
  Sparkles, FileText
} from "lucide-react";

const API_BASE_URL = "http://127.0.0.1:8000/api";

export default function App() {
  // --- State Configuration ---
  const [theme, setTheme] = useState(localStorage.getItem("orchard_theme") || "dark");
  const [username, setUsername] = useState(localStorage.getItem("orchard_username") || null);
  const [apiKey, setApiKey] = useState(localStorage.getItem("orchard_api_key") || null);
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

  // --- Premium PDF States ---
  const [isPremium, setIsPremium] = useState(false);
  const [pdfFiles, setPdfFiles] = useState([]);
  const [isLoadingPdfs, setIsLoadingPdfs] = useState(false);
  const [selectedPdf, setSelectedPdf] = useState(null);
  const [pdfChunks, setPdfChunks] = useState([]);
  const [isLoadingChunks, setIsLoadingChunks] = useState(false);
  const [pdfFileToUpload, setPdfFileToUpload] = useState(null);
  const [isUploadingPdf, setIsUploadingPdf] = useState(false);

  // --- Effects ---
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("orchard_theme", theme);
  }, [theme]);

  useEffect(() => {
    if (apiKey) {
      fetchCollections();
      fetchPremiumStatus();
    }
  }, [apiKey]);

  useEffect(() => {
    if (activeCollection && activeTab === "documents") {
      fetchDocuments();
    } else if (activeCollection && activeTab === "pdf" && isPremium) {
      fetchPdfFiles();
    }
  }, [activeCollection, activeTab, isPremium]);

  // --- Toast Handler ---
  const triggerToast = (message, type = "success") => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3500);
  };

  // --- Premium API Integrations ---
  const fetchPremiumStatus = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/status`, {
        headers: { "x-api-key": apiKey }
      });
      const data = await res.json();
      if (res.ok) {
        setIsPremium(data.is_premium);
      }
    } catch (e) {
      console.error("Failed to fetch premium billing status", e);
    }
  };

  const handleUpgradeToPremium = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/upgrade`, {
        method: "POST",
        headers: { "x-api-key": apiKey }
      });
      const data = await res.json();
      if (res.ok) {
        setIsPremium(true);
        triggerToast(data.message, "success");
      } else {
        triggerToast(data.detail || "Upgrade failed.", "error");
      }
    } catch {
      triggerToast("Error contacting payment gateway simulation.", "error");
    }
  };

  const fetchPdfFiles = async () => {
    setIsLoadingPdfs(true);
    try {
      const res = await fetch(`${API_BASE_URL}/pdf/collections/${activeCollection}/documents`, {
        headers: { "x-api-key": apiKey }
      });
      const data = await res.json();
      setIsLoadingPdfs(false);
      if (res.ok) {
        setPdfFiles(data.documents || []);
      } else {
        triggerToast(data.detail || "Error loading uploaded files.", "error");
      }
    } catch {
      setIsLoadingPdfs(false);
      triggerToast("Network communication error with PDF services.", "error");
    }
  };

  const handlePdfUpload = async (e) => {
    e.preventDefault();
    if (!pdfFileToUpload) {
      triggerToast("Please select a PDF document first.", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file", pdfFileToUpload);

    setIsUploadingPdf(true);
    try {
      const res = await fetch(`${API_BASE_URL}/pdf/collections/${activeCollection}/upload`, {
        method: "POST",
        headers: { "x-api-key": apiKey },
        body: formData
      });
      const data = await res.json();
      setIsUploadingPdf(false);
      if (res.ok) {
        triggerToast(data.message, "success");
        setPdfFileToUpload(null);
        const fileInput = document.getElementById("pdf-file-input");
        if (fileInput) fileInput.value = "";
        fetchPdfFiles();
      } else {
        triggerToast(data.detail || "Upload failed.", "error");
      }
    } catch {
      setIsUploadingPdf(false);
      triggerToast("Error executing PDF scan & upload.", "error");
    }
  };

  const handlePdfDelete = async (sourceId) => {
    const confirmDelete = window.confirm("Are you sure you want to delete this PDF and all its indexed vector chunks?");
    if (!confirmDelete) return;

    try {
      const res = await fetch(`${API_BASE_URL}/pdf/collections/${activeCollection}/documents/${sourceId}`, {
        method: "DELETE",
        headers: { "x-api-key": apiKey }
      });
      const data = await res.json();
      if (res.ok) {
        triggerToast(data.message, "success");
        if (selectedPdf && selectedPdf.source_id === sourceId) {
          setSelectedPdf(null);
          setPdfChunks([]);
        }
        fetchPdfFiles();
      } else {
        triggerToast(data.detail || "Delete failed.", "error");
      }
    } catch {
      triggerToast("Error executing delete command.", "error");
    }
  };

  const fetchPdfChunks = async (pdfObj) => {
    setSelectedPdf(pdfObj);
    setIsLoadingChunks(true);
    try {
      const res = await fetch(`${API_BASE_URL}/pdf/collections/${activeCollection}/documents/${pdfObj.source_id}`, {
        headers: { "x-api-key": apiKey }
      });
      const data = await res.json();
      setIsLoadingChunks(false);
      if (res.ok) {
        setPdfChunks(data.chunks || []);
      } else {
        triggerToast(data.detail || "Failed to load document chunks.", "error");
      }
    } catch {
      setIsLoadingChunks(false);
      triggerToast("Failed to fetch document chunks.", "error");
    }
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
        localStorage.setItem("orchard_username", authUsername.trim());
        localStorage.setItem("orchard_api_key", data.api_key);
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
    localStorage.removeItem("orchard_username");
    localStorage.removeItem("orchard_api_key");
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
      const res = await fetch(`${API_BASE_URL}/vdb/collections/${activeCollection}/upsert_documents`, {
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
    const key = apiKey || "your_orchard_api_key";
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
    "documents": ["OrchardDB wraps ChromaDB securely, providing robust trials."],
    "metadatas": [{"category": "demo"}]
}
requests.post(f"{BASE_URL}/collections/${col}/upsert_documents", headers=HEADERS, json=payload_upsert)

# 2. Perform similarity search query
payload_query = {
    "query_text": "What is OrchardDB?",
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
fetch(\`\${baseUrl}/collections/${col}/upsert_documents\`, {
  method: "POST",
  headers: headers,
  body: JSON.stringify({
    ids: ["item_1"],
    documents: ["OrchardDB is modern and developer-first."],
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
    query_text: "What is OrchardDB?",
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
            <span className="logo-text">Orchard<span className="logo-accent">DB</span></span>
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
                OrchardDB wraps ChromaDB with seamless multi-tenancy, instant API key authorization, and a stunning developer console. Start trial indexing in seconds.
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
                  <span className="browser-title">console.orcharddb.dev</span>
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
                  <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "0.5rem", flexWrap: "wrap" }}>
                    <h2 style={{ margin: 0 }}>Welcome back, <span className="highlight-text">{username}</span>!</h2>
                    {isPremium ? (
                      <span className="badge premium-badge" style={{ background: "linear-gradient(135deg, #f59e0b, #d97706)", color: "#fff", display: "inline-flex", alignItems: "center", gap: "0.25rem", border: "none", fontSize: "0.75rem", padding: "0.1rem 0.5rem", borderRadius: "100px", fontWeight: "600" }}>
                        <Sparkles size={12} /> Premium
                      </span>
                    ) : (
                      <button className="btn btn-outline" style={{ height: "24px", padding: "0 0.5rem", fontSize: "0.7rem", display: "inline-flex", alignItems: "center", gap: "0.25rem", color: "#f59e0b", borderColor: "#f59e0b", background: "transparent", fontWeight: "600", cursor: "pointer", borderRadius: "4px" }} onClick={handleUpgradeToPremium}>
                        <Sparkles size={12} /> Upgrade to Premium
                      </button>
                    )}
                  </div>
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
                      <div className="sandbox-tabs" style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem" }}>
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
                          className={`tab-btn ${activeTab === "pdf" ? "active" : ""}`}
                          style={{ display: "flex", alignItems: "center", gap: "0.25rem" }}
                          onClick={() => {
                            setActiveTab("pdf");
                            if (isPremium) fetchPdfFiles();
                          }}
                        >
                          <Sparkles size={12} style={{ color: "#f59e0b" }} />
                          <span>PDF Scan & Load</span>
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

                      {/* Tab Content: Premium PDF Scan & Load */}
                      {activeTab === "pdf" && (
                        <div className="tab-content">
                          {!isPremium ? (
                            <div className="premium-lock-overlay" style={{
                              background: "rgba(30, 27, 75, 0.4)",
                              backdropFilter: "blur(8px)",
                              borderRadius: "12px",
                              padding: "3rem 2rem",
                              textAlign: "center",
                              border: "1px solid rgba(245, 158, 11, 0.2)",
                              margin: "1rem 0"
                            }}>
                              <div style={{ display: "inline-flex", padding: "1rem", borderRadius: "50%", background: "rgba(245, 158, 11, 0.1)", marginBottom: "1.5rem" }}>
                                <Lock size={40} style={{ color: "#f59e0b" }} />
                              </div>
                              <h3 style={{ fontSize: "1.5rem", margin: "0 0 0.5rem 0", color: "#fff" }}>Unlock Premium Document Services</h3>
                              <p style={{ maxWidth: "500px", margin: "0 auto 1.5rem auto", color: "var(--text-muted)", fontSize: "0.95rem", lineHeight: "1.5" }}>
                                Parse entire PDF documents into semantically coherent vector chunks, map text blocks back to their exact source pages, and index complex manuals in seconds.
                              </p>
                              <div style={{ display: "flex", justifyContent: "center", gap: "1.5rem", flexWrap: "wrap", marginBottom: "2rem" }}>
                                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", color: "#e2e8f0" }}>
                                  <Sparkles size={14} style={{ color: "#f59e0b" }} />
                                  <span>Semantic Parsing</span>
                                </div>
                                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", color: "#e2e8f0" }}>
                                  <Sparkles size={14} style={{ color: "#f59e0b" }} />
                                  <span>Page-Level Mapping</span>
                                </div>
                                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", fontSize: "0.85rem", color: "#e2e8f0" }}>
                                  <Sparkles size={14} style={{ color: "#f59e0b" }} />
                                  <span>Bulk Ingestion</span>
                                </div>
                              </div>
                              <button 
                                className="btn btn-primary" 
                                style={{ background: "linear-gradient(135deg, #f59e0b, #d97706)", border: "none", color: "#fff", padding: "0.75rem 2rem", fontSize: "1rem", fontWeight: "600", borderRadius: "8px", boxShadow: "0 4px 12px rgba(245, 158, 11, 0.25)", cursor: "pointer" }}
                                onClick={handleUpgradeToPremium}
                              >
                                Upgrade Account (Instant Access)
                              </button>
                            </div>
                          ) : (
                            <div className="pdf-service-playground" style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: "1.5rem" }}>
                                
                                {/* PDF Ingestion Card */}
                                <div className="form-container" style={{ margin: 0 }}>
                                  <h4>Ingest PDF Document</h4>
                                  <p className="section-desc">Upload a PDF to parse pages semantically and automatically index their chunks into the current collection.</p>
                                  
                                  <form onSubmit={handlePdfUpload} style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                                    <div 
                                      className="file-upload-zone"
                                      style={{
                                        border: "2px dashed var(--border-color)",
                                        borderRadius: "8px",
                                        padding: "2rem 1rem",
                                        textAlign: "center",
                                        background: "var(--card-bg-light)",
                                        cursor: "pointer",
                                        transition: "border-color 0.2s"
                                      }}
                                      onClick={() => document.getElementById("pdf-file-input").click()}
                                    >
                                      <CloudUpload size={32} style={{ color: "var(--text-muted)", marginBottom: "0.5rem" }} />
                                      {pdfFileToUpload ? (
                                        <div>
                                          <p style={{ fontWeight: "600", margin: "0 0 0.25rem 0", color: "var(--text-main)" }}>{pdfFileToUpload.name}</p>
                                          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", margin: 0 }}>{(pdfFileToUpload.size / 1024).toFixed(1)} KB</p>
                                        </div>
                                      ) : (
                                        <div>
                                          <p style={{ fontWeight: "500", margin: "0 0 0.25rem 0" }}>Click to select PDF manual</p>
                                          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", margin: 0 }}>Max file size: 10MB</p>
                                        </div>
                                      )}
                                      <input 
                                        type="file" 
                                        id="pdf-file-input"
                                        accept=".pdf"
                                        style={{ display: "none" }}
                                        onChange={(e) => setPdfFileToUpload(e.target.files[0])}
                                      />
                                    </div>
                                    
                                    <button 
                                      type="submit" 
                                      className="btn btn-primary" 
                                      disabled={isUploadingPdf || !pdfFileToUpload}
                                      style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "0.5rem" }}
                                    >
                                      {isUploadingPdf ? (
                                        <>
                                          <RotateCw className="animate-spin" size={16} />
                                          <span>Parsing & Chunking PDF...</span>
                                        </>
                                      ) : (
                                        <>
                                          <CloudUpload size={16} />
                                          <span>Upload & Scan PDF</span>
                                        </>
                                      )}
                                    </button>
                                  </form>
                                </div>

                                {/* Processed PDFs Registry */}
                                <div className="form-container" style={{ margin: 0, display: "flex", flexDirection: "column" }}>
                                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                                    <h4 style={{ margin: 0 }}>Document Registry</h4>
                                    <button onClick={fetchPdfFiles} className="icon-btn" title="Refresh files" disabled={isLoadingPdfs}>
                                      <RotateCw className={isLoadingPdfs ? "animate-spin" : ""} size={14} />
                                    </button>
                                  </div>
                                  
                                  {isLoadingPdfs ? (
                                    <div style={{ display: "flex", justifyContent: "center", padding: "3rem" }}>
                                      <RotateCw className="animate-spin" size={24} />
                                    </div>
                                  ) : pdfFiles.length === 0 ? (
                                    <div style={{ textAlign: "center", padding: "2.5rem 1rem", color: "var(--text-muted)", background: "rgba(0, 0, 0, 0.05)", borderRadius: "8px", flex: 1, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center" }}>
                                      <FileText size={24} style={{ marginBottom: "0.5rem" }} />
                                      <p style={{ margin: 0, fontSize: "0.9rem" }}>No PDFs ingested in this space yet.</p>
                                    </div>
                                  ) : (
                                    <div style={{ overflowY: "auto", maxHeight: "250px", display: "flex", flexDirection: "column", gap: "0.5rem", flex: 1 }}>
                                      {pdfFiles.map(file => (
                                        <div 
                                          key={file.source_id} 
                                          onClick={() => fetchPdfChunks(file)}
                                          style={{
                                            display: "flex",
                                            alignItems: "center",
                                            justifyContent: "space-between",
                                            padding: "0.75rem",
                                            background: selectedPdf?.source_id === file.source_id ? "rgba(245, 158, 11, 0.1)" : "var(--card-bg-light)",
                                            border: selectedPdf?.source_id === file.source_id ? "1px solid rgba(245, 158, 11, 0.3)" : "1px solid var(--border-color)",
                                            borderRadius: "6px",
                                            cursor: "pointer",
                                            transition: "all 0.15s"
                                          }}
                                        >
                                          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", minWidth: 0 }}>
                                            <FileText size={16} style={{ color: "#f59e0b", flexShrink: 0 }} />
                                            <div style={{ minWidth: 0 }}>
                                              <p style={{ fontWeight: "600", fontSize: "0.85rem", margin: 0, textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap" }}>{file.doc_name}</p>
                                              <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", margin: 0 }}>ID: {file.source_id} • {new Date(file.created_at).toLocaleDateString()}</p>
                                            </div>
                                          </div>
                                          <button 
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handlePdfDelete(file.source_id);
                                            }}
                                            className="icon-btn" 
                                            style={{ color: "var(--danger-color)", padding: "0.25rem" }}
                                            title="Delete PDF source"
                                          >
                                            <Trash2 size={14} />
                                          </button>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              </div>

                              {/* Vector Chunk Registry Viewer */}
                              {selectedPdf && (
                                <div className="form-container" style={{ margin: 0 }}>
                                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                                      <Sparkles size={16} style={{ color: "#f59e0b" }} />
                                      <h4 style={{ margin: 0 }}>Processed Semantic Chunks: <span className="highlight-text">{selectedPdf.doc_name}</span></h4>
                                    </div>
                                    <span className="badge" style={{ fontSize: "0.75rem" }}>{pdfChunks.length} chunks</span>
                                  </div>

                                  {isLoadingChunks ? (
                                    <div style={{ display: "flex", justifyContent: "center", padding: "4rem" }}>
                                      <RotateCw className="animate-spin" size={24} />
                                    </div>
                                  ) : pdfChunks.length === 0 ? (
                                    <p style={{ textAlign: "center", color: "var(--text-muted)", padding: "2rem" }}>No text chunks returned for this document.</p>
                                  ) : (
                                    <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem", maxHeight: "400px", overflowY: "auto", paddingRight: "0.25rem" }}>
                                      {pdfChunks.map((chunk, index) => (
                                        <div key={chunk.id} style={{ padding: "1rem", background: "var(--card-bg-light)", border: "1px solid var(--border-color)", borderRadius: "8px" }}>
                                          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.5rem" }}>
                                            <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "var(--text-muted)" }}>ID: {chunk.id}</span>
                                            <span className="badge" style={{ background: "rgba(245, 158, 11, 0.1)", color: "#f59e0b", border: "1px solid rgba(245, 158, 11, 0.2)", fontSize: "0.7rem", padding: "0.1rem 0.4rem" }}>
                                              Page {chunk.metadata?.page !== undefined ? chunk.metadata.page : "N/A"}
                                            </span>
                                          </div>
                                          <p style={{ margin: 0, fontSize: "0.85rem", lineHeight: "1.6", color: "var(--text-main)", whiteSpace: "pre-wrap" }}>{chunk.text}</p>
                                        </div>
                                      ))}
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          )}
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
        <p>&copy; 2026 OrchardDB. Built for lightweight vector database trials. Powered by ChromaDB.</p>
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
                    placeholder="e.g. dev_orchard" 
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
