# ReaderPath

[![Live Demo](https://img.shields.io/badge/Live%20Demo-View-brightgreen)](https://your-deployed-link.com) 
[![GitHub license](https://img.shields.io/github/license/nagolbuchan/reader-path)](LICENSE)

**A personalized learning platform that turns any topic into a structured course of real books and thoughtful written assignments.**  
No AI-generated summaries — just curated resources designed to make users active readers and thinkers.

## ✨ Features

### MVP (Current / In Progress)
- Topic input → AI-generated structured course (4–6 modules) with real books and written research assignments
- Multi-agent CrewAI system for intelligent book discovery (prioritizing quality sources)
- Neo4j graph database for storing courses, modules, books, authors, and basic user progress
- Personalized recommendations that avoid books the user has already read (when history exists)
- Responsive React frontend with module navigation and rich-text assignment editor
- Dynamic addition of newly discovered books to the shared graph database
- Local development setup with Docker Compose

### Planned / Future Features
- **Contrast / Balanced View Mode** — Optional generation of opposing perspectives (e.g., Federalist vs Anti-Federalist book lists)
- **User Bias / Perspective Selection** — Allow users to specify a side or viewpoint during topic entry when relevant
- **Interactive Course Editor Agent** — Conversational agent for refining courses in real-time (add/remove books, adjust focus, etc.)
- **Advanced Personalization & Gates** — Stronger reading history integration; require written responses (especially to opposing views) before unlocking new courses
- **User-Facing Agents** — Email summaries, progress reports, and notifications
- **Social Graph Features** — Connect users by shared books read; author grouping by genre/topic/argument stance
- **Engagement Incentives** — Streaks, badges, or expanded access for consistent writing and intellectual engagement
- **Public sharing** of courses and improved export options

## 🛠️ Tech Stack

**Frontend**  
- React 19 + TypeScript + Vite  
- Tailwind CSS + shadcn/ui  
- TanStack Query + React Router  

**Backend**  
- FastAPI (Python)  
- CrewAI (multi-agent system)  

**Data & AI**  
- Neo4j graph database  
- OpenAI / Groq / Anthropic (via CrewAI)  

**DevOps**  
- Docker Compose (local development)  
- Deployed on Vercel (frontend) + Railway/Render (backend) + Neo4j Aura  

## 🗺️ Roadmap

- [ ] Core course generation with CrewAI + Neo4j storage
- [ ] Responsive frontend UI + basic progress tracking
- [ ] User authentication & persistent course saving
- [ ] Assignment submission & review system
- [ ] Contrast view mode + perspective selection
- [ ] Interactive course editor agent
- [ ] Writing engagement gates & incentives
- [ ] Public course sharing

## 🚀 Quick Start (Local Development)

### Prerequisites
- Node.js 20+
- Python 3.11+
- Neo4j (Aura free tier or local)
- OpenAI/Groq API key

### 1. Clone the repo
```bash
git clone https://github.com/nagolbuchan/reader-path.git
cd reader-path

### 2. Backend
cd backend
python -m venv venv
source venv/bin/activate    # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Add your API keys
uvicorn main:app --reload

### 3. Frontend
cd ../frontend
npm install
npm run dev

Open http://localhost:5173
