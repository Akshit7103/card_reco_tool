# 🏦 Configuration-Driven Card Reconciliation Tool

A powerful, extensible reconciliation tool for financial data comparison with a modern configuration-driven architecture.

## ✨ Features

- **🔧 Configuration-Driven Architecture**: Easily add new reconciliation types without code changes
- **📊 Multiple Reconciliation Types**: 
  - Bank Statement vs VISA Settlement
  - VISA Detailed vs Summary Report  
  - CMS vs VISA Comparison
- **🎨 Dynamic UI**: Forms generated automatically from configuration
- **📈 Smart Processing**: Auto-detection of file headers and column mapping
- **💾 Export Functionality**: Download results in Excel format
- **🔍 API Endpoints**: RESTful API for integration
- **🛡️ Error Handling**: Comprehensive validation and user-friendly error messages

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/Akshit7103/card_reco_tool.git
   cd card_reco_tool
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   ```
   http://localhost:5000
   ```

## 📁 Project Structure

```
card_reco_tool/
├── app.py                 # Main Flask application
├── config.py              # Configuration-driven settings
├── processors.py          # Dynamic processing system
├── reconcile.py           # Core reconciliation logic
├── requirements.txt       # Python dependencies
├── templates/
│   ├── index_dynamic.html # Dynamic form template
│   └── error.html         # Error page template
└── static/
    └── style.css          # Enhanced styling
```

## 🔧 Configuration

All reconciliation types are defined in `config.py`. To add a new reconciliation type:

```python
"new_reconciliation": {
    "name": "New Reconciliation Type",
    "description": "Description of what this reconciliation does",
    "files": [
        {
            "field_name": "file1",
            "label": "First File (Excel)",
            "accept": ".xlsx,.xls",
            "required": True
        }
    ],
    "processor": "process_new_reconciliation",
    "result_template": "new_reconciliation"
}
```

## 📡 API Endpoints

- `GET /` - Main application interface
- `GET /api/reconciliation-types` - Get all available reconciliation types
- `GET /health` - Health check endpoint
- `POST /` - Process reconciliation
- `GET /download` - Download reconciliation results

## 🌐 Deployment

### Render Deployment

1. **Connect your GitHub repository** to Render
2. **Set the following build settings**:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Environment**: Python 3

### Environment Variables

No environment variables are required for basic functionality.

## 📊 Supported File Formats

- **Excel Files**: `.xlsx`, `.xls`
- **Text Files**: `.txt`
- **Encodings**: UTF-8, Latin1, CP1252

## 🛠️ Technical Features

- **Dynamic Column Detection**: Automatically maps column names using fuzzy matching
- **Multi-encoding Support**: Handles different file encodings automatically
- **Temporary File Management**: Secure file handling with automatic cleanup
- **Responsive Design**: Works on desktop and mobile devices
- **Error Recovery**: Graceful handling of malformed files

## 🔍 Data Processing

The tool supports various data validation and processing features:

- Header auto-detection
- Column name normalization
- Data type validation
- Missing value handling
- Duplicate detection

## 📈 Future Enhancements

- Machine Learning integration for smart column detection
- Real-time processing with progress indicators
- Advanced visualization dashboards
- User authentication and role management
- Database persistence for audit trails

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the `/health` endpoint for system status
- Review the configuration in `config.py`

---

**Built with ❤️ using Flask, Pandas, and configuration-driven architecture**