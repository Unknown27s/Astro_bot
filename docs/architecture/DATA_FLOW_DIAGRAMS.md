# AstroBot Data Flow Diagrams

These Mermaid diagrams illustrate the core data flows of the AstroBot system. You can copy the code blocks below and paste them into [Mermaid Live Editor](https://mermaid.live/), Notion, or PPT plugins to generate visual diagrams for your presentation.

## 1. Complete System Architecture & Data Flow overview 

This high-level diagram shows how all the components of the three-tier architecture communicate.

```mermaid
graph TD
    %% Define Styles
    classDef frontend fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:white;
    classDef backend fill:#10b981,stroke:#047857,stroke-width:2px,color:white;
    classDef database fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:white;
    classDef user fill:#64748b,stroke:#475569,stroke-width:2px,color:white;

    %% Users
    subgraph Users ["👤 Users"]
        direction LR
        User_Admin((Admin / Faculty)):::user
        User_Student((Student / User)):::user
    end

    %% Presentation Layer
    subgraph Presentation ["💻 Presentation Layer"]
        direction LR
        UI_Streamlit["Streamlit UI<br/>(Admin)"]:::frontend
        UI_React["React Frontend<br/>(Web App)"]:::frontend
        UI_SpringBoot["Spring Boot API<br/>(Integrations)"]:::frontend
    end

    %% Application Layer
    subgraph Application ["⚙️ Application Layer (FastAPI & RAG)"]
        direction LR
        API_Fast["FastAPI REST Server"]:::backend
        Auth["Auth & Sessions"]:::backend
        V2T["Whisper Transcription<br/>(Voice)"]:::backend
        
        subgraph Pipeline ["🧠 RAG Pipeline"]
            direction LR
            Ingest["Document Ingestion<br/>(Parser, Chunker, Embedder)"]:::backend
            Retrieve["Retriever<br/>(Search & Context)"]:::backend
            Gen["Generator<br/>(LLM / Ollama)"]:::backend
        end
    end

    %% Data Layer
    subgraph Data ["💾 Data Layer (Storage)"]
        direction LR
        FS_Storage[("File System<br/>(PDFs/Docs)")]:::database
        DB_Chroma[("ChromaDB<br/>(Vectors)")]:::database
        DB_SQLite[("SQLite<br/>(Users/Logs)")]:::database
    end

    %% Flow Dynamics
    User_Admin -- "Uploads" --> UI_Streamlit
    User_Student -- "Web Chat" --> UI_React
    User_Student -- "API Auth" --> UI_SpringBoot

    UI_Streamlit -- HTTP --> API_Fast
    UI_React -- HTTP --> API_Fast
    UI_SpringBoot -- HTTP --> API_Fast

    API_Fast --> Auth
    API_Fast -- "Audio" --> V2T
    API_Fast -- "Upload" --> Ingest
    API_Fast -- "Query" --> Retrieve
    API_Fast -- "Answer Data" --> Gen

    V2T -- "Text" --> Retrieve
    Retrieve -- "Context" --> Gen

    Auth <--> DB_SQLite
    Ingest -- "Save Doc" --> FS_Storage
    Ingest -- "Save Meta" --> DB_SQLite
    Ingest -- "Save Vector" --> DB_Chroma
    
    Retrieve -- "Search Nearest" --> DB_Chroma
    Gen -- "Log Query" --> DB_SQLite
```

---

## 2. Document Upload (Ingestion) Flow

This diagram explains the step-by-step process of what happens when a document is uploaded. This is the **Preparation Phase**.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as 👨‍🏫 Faculty / Admin
    participant UI as 🖥️ UI (Streamlit/React)
    participant API as ⚙️ FastAPI
    participant Parser as 📄 Parser
    participant Chunker as ✂️ Chunker
    participant Embedder as 🔢 Embedder
    participant ChromaDB as 🗄️ ChromaDB
    participant SQLite as 🗃️ SQLite DB

    Admin->>UI: Uploads Document (e.g., Syllabus.pdf)
    UI->>API: Send File Data
    API->>SQLite: Log pending document upload
    
    API->>Parser: Extract text & structure
    Note right of Parser: Extracts raw text ignoring formatting
    Parser-->>API: Return raw text
    
    API->>Chunker: Split text into pieces
    Note right of Chunker: structural splits & 500-char chunks (50 overlap)
    Chunker-->>API: Return text chunks + metadata
    
    API->>Embedder: Convert chunks to vectors
    Note right of Embedder: uses all-MiniLM-L6-v2 (384 dims)
    Embedder-->>API: Return embedding arrays
    
    API->>ChromaDB: Store vectors & text & metadata
    ChromaDB-->>API: Confirmation
    
    API->>SQLite: Mark document as 'processed'
    API-->>UI: Return Success Checkmark
    UI-->>Admin: "Document successfully processed!"
```

---

## 3. User Query & Retrieval (RAG) Flow

This diagram is great for showing how the Bot answers questions based on existing knowledge.

```mermaid
flowchart TD
    classDef start fill:#10b981,stroke:#047857,color:white;
    classDef process fill:#3b82f6,stroke:#1d4ed8,color:white;
    classDef llm fill:#8b5cf6,stroke:#5b21b6,color:white;
    classDef db fill:#f59e0b,stroke:#b45309,color:white;
    classDef endNode fill:#ec4899,stroke:#be185d,color:white;

    Start((👤 User Asks Question)):::start

    InputCheck{Is Input Voice?}:::process
    Voice[🎙️ Whisper Transcribes Voice to Text]:::process
    
    TextQuery["💬 Get Text Query<br/>(e.g., 'When is the midterm?')"]:::process
    
    EmbedQ["🔢 Convert Query to Vector<br/>(Embedder)"]:::process
    
    SearchDB[("🗄️ Search ChromaDB<br/>Find top 5 closest vectors")]:::db
    
    FormatContext["📄 Format Context<br/>Combine chunks + Source metadata"]:::process
    
    CallLLM{"🤖 Apply LLM AI<br/>(Local Ollama or Grok/Gemini)"}:::llm
    
    GenerateAns["✏️ Generate Answer<br/>(Based ONLY on provided context)"]:::process
    
    FormatAns["🔗 Attach Citations<br/>Add Source list"]:::process
    
    LogAction[("🗃️ Log to SQLite")]:::db
    
    End((✅ Deliver Answer to User)):::endNode

    %% Connections
    Start --> InputCheck
    InputCheck -- Yes --> Voice
    Voice --> TextQuery
    InputCheck -- No --> TextQuery
    
    TextQuery --> EmbedQ
    EmbedQ --> SearchDB
    SearchDB -->|"Returns Top Chunks"| FormatContext
    FormatContext --> CallLLM
    CallLLM --> GenerateAns
    GenerateAns --> FormatAns
    FormatAns --> LogAction
    LogAction --> End
```
