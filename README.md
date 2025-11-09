# hackCBS - AI-Driven DB RAG & Analytics

**Python version:** 3.12

An intelligent database assistant that leverages RAG (Retrieval-Augmented Generation) technology to provide natural language querying, schema discovery, and analytics for your databases. Built with Flask, ChromaDB, and Google's Gemini AI.

## 🌟 Features

- **Natural Language Database Queries**: Ask questions about your data in plain English
- **Intelligent Schema Discovery**: Automatically analyzes and understands your database structure
- **RAG-Powered Responses**: Uses ChromaDB for context-aware query generation
- **Multi-Database Support**: Works with PostgreSQL, MySQL, and other SQL databases
- **PDF Document Processing**: Upload and query PDF documents alongside your database
- **Real-time Analytics**: Generate insights and visualizations from your data
- **Interactive Data Visualizations**: 
  - Dynamic charts and graphs using Chart.js
  - Real-time data plotting and analysis
  - Customizable visualization types (bar, line, pie, scatter plots)
  - Export visualizations as images
- **Dashboard Analytics**: Comprehensive data insights with visual representations
- **Cloud-Ready Deployment**: Easy deployment to Google Cloud Run
- **Secure**: Environment-based configuration with secret management

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API      │    │   Database      │
│   (Web UI)      │◄──►│   - Query Engine │◄──►│   - PostgreSQL  │
│   - Chart.js    │    │   - RAG System   │    │   - MySQL       │
│   - Visualizations   │   - Analytics    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   ChromaDB       │
                    │   (Vector Store) │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Gemini AI      │
                    │   (LLM)          │
                    └──────────────────┘
```

## 🚀 Quick Start

1. **Setup Environment:**
   ```bash
   chmod +x run.sh
   ./run.sh
   ```


2. **Start the Application:**
   ```bash
   python app.py
   ```

## 📊 Visualization Features

- **Interactive Charts**: Dynamic data visualization using Chart.js
- **Multiple Chart Types**: Bar charts, line graphs, pie charts, scatter plots
- **Real-time Updates**: Live data visualization as queries are executed
- **Export Capabilities**: Download charts as PNG/PDF
- **Responsive Design**: Optimized for desktop and mobile viewing
- **Custom Styling**: Themed visualizations matching your data insights

## 🛠️ Technology Stack

- **Backend**: Flask (Python 3.12)
- **Database**: PostgreSQL, MySQL support
- **Vector Database**: ChromaDB
- **AI/ML**: Google Gemini API
- **Visualization**: Chart.js, D3.js
- **Frontend**: HTML5, CSS3, JavaScript
- **Containerization**: Docker
- **Cloud**: Google Cloud Run
- **Security**: Secret Manager, Environment variables

## 📋 Requirements

- Python 3.12+
- Docker (optional)
- Google Cloud SDK (for cloud deployment)
- Database (PostgreSQL/MySQL)
- Gemini API key

## 🆘 Support

For support and questions:
- Create an issue in this repository
- Contact the development team

---

Built with ❤️ for hackCBS 2025