# 🤖 AI Resume Analyzer & Hiring Intelligence Platform

A production-level AI Resume Analyzer that uses NLP and ML to analyze resumes, match them with job descriptions, predict hiring decisions, and provide AI-based suggestions — all using FREE and open-source tools.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **📄 Resume Parsing** | Extract text and structured data from PDF/DOCX files |
| **🔍 Semantic Matching** | Compare resumes to job descriptions using sentence-transformers |
| **🛠️ Skill Extraction** | Categorize and extract skills using spaCy NER |
| **🎯 Hiring Decision Engine** | ML-based prediction: Hire / Shortlist / Reject |
| **✅ ATS Checker** | Check resume compatibility with Applicant Tracking Systems |
| **📊 Interactive Dashboard** | Streamlit UI with visualizations |
| **🔌 REST API** | FastAPI backend for programmatic access |
| **💼 Multi-Source Job Search** | Fetch jobs from Remotive, Unstop, Internshala, & Glassdoor |

---

## 🏗️ Tech Stack (All FREE)

- **Python 3.8+**
- **NLP/ML**: spaCy, sentence-transformers, scikit-learn, transformers
- **Resume Parsing**: PyPDF2, python-docx
- **Web**: FastAPI, Streamlit
- **Visualization**: Plotly
- **Database**: SQLAlchemy (optional)

---

## 📁 Project Structure

```
project/
├── data/                    # Data storage
├── models/                  # Saved models
├── src/
│   ├── parser.py           # Resume parsing (PDF/DOCX)
│   ├── matcher.py          # Semantic matching
│   ├── skill_extractor.py  # Skill extraction & categorization
│   ├── classifier.py       # Resume classification (TF-IDF + ML)
│   ├── decision_engine.py  # Hiring decision prediction
│   ├── ats_checker.py      # ATS compatibility checker
│   ├── job_fetcher.py      # Job data from free APIs
│   └── api.py              # FastAPI backend
├── app/
│   └── streamlit_app.py    # Streamlit dashboard
├── requirements.txt        # Dependencies
└── README.md              # This file
```

---

## 🚀 Quick Start

### 1. Clone & Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 3. Run Streamlit Dashboard

```bash
streamlit run app/streamlit_app.py
```

The dashboard will open at `http://localhost:8501`

### 4. Run FastAPI Server (Optional)

```bash
uvicorn src.api:app --reload
```

API will be available at `http://localhost:8000`

---

## 📖 Usage Guide

### Option 1: Streamlit Dashboard

1. **Single Resume Analysis**
   - Upload a resume (PDF/DOCX)
   - Paste a job description
   - Click "Analyze Resume"
   - View match scores, decision, and recommendations

2. **Batch Ranking**
   - Upload multiple resumes
   - Provide job description
   - Get ranked candidate list

3. **Job Search**
   - Search for remote jobs
   - Use keywords and filters

4. **ATS Checker**
   - Check resume ATS compatibility
   - Get improvement suggestions

### Option 2: REST API

```bash
# Full analysis endpoint
curl -X POST "http://localhost:8000/api/full-analysis" \
  -F "file=@resume.pdf" \
  -F "job_description=Job description text..."
```

---

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.env` file:

```env
# Adzuna API (optional - for more job data)
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key

# Database (optional)
DATABASE_URL=postgresql://user:pass@localhost/resume_analyzer
```

---

## 📊 Sample Output

```
🎯 Match Score: 82%
🎬 Decision: Shortlist
⚠️ Confidence: Medium

✅ Matched Skills:
   • Python
   • SQL
   • Data Analysis

❌ Missing Skills:
   • Machine Learning
   • AWS

💡 Recommendations:
   • Learn AWS fundamentals
   • Add ML projects to portfolio
   • Quantify achievements
```

---

## 🧠 How It Works

### 1. Resume Parsing
- Extract text from PDF/DOCX using PyPDF2 and python-docx
- Parse structured data: name, email, skills, education, experience

### 2. Semantic Matching
- Use `sentence-transformers` (all-MiniLM-L6-v2) for embeddings
- Calculate cosine similarity between resume and job description

### 3. Skill Extraction
- Use spaCy NER and pattern matching
- Categorize skills into: Programming, Web, Data Science, Cloud, etc.

### 4. Hiring Decision
- Combine match scores with resume quality indicators
- Use Gradient Boosting classifier for decision prediction

### 5. ATS Checking
- Check for required sections
- Detect formatting issues (tables, images, etc.)
- Analyze keyword density

---

## ⚠️ Limitations

- Free APIs have rate limits
- ML models need training data for best results
- Resume parsing accuracy depends on document formatting

---

## 📝 License

MIT License

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 🙏 Acknowledgments

- [sentence-transformers](https://sbert.net/) - Semantic embeddings
- [spaCy](https://spacy.io/) - NLP processing
- [Remotive API](https://remotive.com/api) - Free job listings
- [Streamlit](https://streamlit.io/) - Dashboard framework