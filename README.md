# 🍎 OrchardDB

OrchardDB is a scalable, multi-tenant Vector Database Platform designed specifically for powering Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG) applications. It provides developers with isolated vector collections, built-in ML embedding generation (ONNX), 3D vector visualizations (PCA/t-SNE), and secure API key management.

## 🏗️ Current State: The Microservices Migration
OrchardDB was initially built as a modular monolith (a React frontend paired with a single FastAPI backend handling all logic). 

**What is currently going on?**
We are actively migrating the platform into a true **Distributed Microservices Architecture**. Heavy workloads (like processing 100MB PDF files, running ML text chunking, and embedding generation) were causing HTTP timeouts and memory spikes in the main API server.

To solve this, we are currently executing **Phase 1** of our migration:
- Introduced a **Redis Message Broker**.
- Stripped the heavy `pypdf` logic out of the core API.
- Created a completely standalone **Celery PDF Worker Microservice** (`backend/services/pdf_worker_service`).
- The Core API now instantly responds to uploads with a `202 Accepted` and offloads the processing to the background worker.

## 🚀 Roadmap & Future Vision
OrchardDB is an **actively evolving platform**. While we are currently focused on fortifying our distributed architecture, we have an exciting pipeline of upcoming features aimed at making this the ultimate open-source Vector DB experience:

### ✨ Tentative Upcoming Features
- **Multi-Modal Support**: Expanding ingestion beyond PDFs to include images, audio, and direct web scraping.
- **Advanced RAG Capabilities**: Built-in hybrid search (keyword + semantic) and automatic query expansion.
- **Analytics Dashboard**: Real-time telemetry on query latency, vector hit rates, and API key usage.
- **Pluggable Embedding Models**: Bring your own models (OpenAI, Cohere, HuggingFace) natively into the ingestion pipeline.

### 🏗️ Architectural Evolution
As we scale these features, the underlying architecture is transitioning into a highly resilient, Kubernetes-ready **Microservices Mesh**:
1. **API Gateway**: A unified entry point (Kong/Nginx) for intelligent rate-limiting.
2. **Auth & Identity Service**: Dedicated PostgreSQL instances for robust tenant management.
3. **Vector Orchestrator**: Direct, high-speed RPC connections to a distributed ChromaDB cluster.
4. **Auto-Scaling Workers**: Event-driven Celery workers that automatically spin up/down based on Redis queue depth.
5. **Compute-Optimized Visualizer**: Standalone ML microservices dedicated entirely to running heavy dimensionality reduction algorithms.

---

## 💻 Local Development Setup

Because OrchardDB is now a distributed system, you must run three separate components concurrently to test the platform locally and one more for frontend.

### 1. Start the Redis Message Broker
Redis acts as the central communication hub between the microservices.
```bash
docker run -d -p 6379:6379 redis:latest
```

### 2. Start the Core API
This is the main FastAPI application serving the React frontend.
```bash
cd backend
venv\Scripts\activate
python run.py
```

### 3. Start the PDF Worker Microservice
This background service listens to Redis and processes all PDF document uploads independently.
```bash
cd backend\services\pdf_worker_service
..\..\venv\Scripts\activate

# On Windows, --pool=solo is required for Celery
celery -A worker.celery_app worker --loglevel=info --pool=solo
```

### 4. Start the Frontend
The React application dashboard.
```bash
cd frontend
npm run dev
```

---

## 🔒 Security
- **Tenant Isolation**: Every vector collection is strictly scoped to the developer's `tenant_id`.
- **IDOR Prevention**: All tracked documents use unpredictable 10-character cryptographically secure string identifiers instead of sequential integers.
- **JWT Authentication**: For all API endpoints with a 1 hour timeout.

## 🛠️ Current Tech Stack

### Backend & Microservices
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![ChromaDB](https://img.shields.io/badge/ChromaDB-F05A28?style=for-the-badge)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![Celery](https://img.shields.io/badge/celery-%23a9cc54.svg?style=for-the-badge&logo=celery&logoColor=f9f7f6)

### Machine Learning & Data Processing
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![NumPy](https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-%23F7931E.svg?style=for-the-badge&logo=scikit-learn&logoColor=white)

### Frontend
![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![Vite](https://img.shields.io/badge/vite-%23646CFF.svg?style=for-the-badge&logo=vite&logoColor=white)