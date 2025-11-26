# Financial Document Analyser and Insights Engine
## Automated Financial Analysis, KPI Extraction & MDA Summarization

## 🚀 Live Demo:
### Frontend: https://financial-insight-engine-1.onrender.com
### Backend API: https://financial-insight-engine.onrender.com/docs

Financial Document Analyser and Insights Engine is a web application that automatically extracts insights from RHP (Red Herring Prospectus) PDF documents.
The tool processes uploaded PDFs to generate:

- 📈 Financial KPIs (Revenue, Profit, Cash Flow, Assets, Ratios…)
- 📊 Interactive Charts (Trends, Balance Sheet Distribution, P&L, Ratios)
- 📰 Latest Company News
- ✍️ TextRank-based MDA Summary
- 🔍 TOC-driven MDA Extraction

The system is fully automated:
Upload PDF → Extract → Analyze → Summarize → Visualize.


## ✨ Features

### 📁 PDF Upload & Storage
- Upload raw RHP PDFs
- Validated for size/format
- Stored with unique file_id

### 📊 Financial Data Extraction
- Automated extraction of key financial metrics (Revenue, EBITDA, Assets, Liabilities)
- Year-over-year trend analysis
- Balance sheet and P&L statement parsing
- KPI identification and calculation

### 🎨 Interactive Dashboard
- Real-time financial charts and visualizations
- KPI cards with important metrics
- Trend analysis with area charts
- Balance sheet distribution pie charts

  
### 📝 Text Summarization
- Management Discussion & Analysis (MDA) section detection
- TextRank algorithm for concise summaries
- Bullet-point format for easy reading

### 📁 File Management
- PDF upload with validation
- Upload history and file management
- Cached results for instant access





## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PDFPlumber & pdfminer.six** - PDF text extraction
- **NLTK** - Natural language processing
- **TextRank** - Graph-based summarization algorithm
- **Python-dotenv** - Environment configuration
- **httpx** - For calling News API

### Frontend
- **React** - User interface library
- **Vite** - Fast build tool and dev server
- **Chart.js** - Data visualization
- **Axios** - HTTP client for API calls

### Deployment
- **Render** - Cloud platform hosting for both backend and frontend

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Backend Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/financial-insight-engine.git
cd financial-insight-engine/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
## 🔮 Future Enhancements

- OCR pipeline for scanned PDFs
- Better financial table detection using ML
- Multi-language support
- Option to export summary + KPIs as PDF
- Compare two companies side-by-side
- Add LLM-based natural-language Q&A

## Team Members
- Shivam Gupta
- Keshav Laddha
  
Built with ❤️ for simplifying financial document analysis.

