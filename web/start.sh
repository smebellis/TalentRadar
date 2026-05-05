#!/bin/sh
echo ""
echo "============================================"
echo "  Job Search Agent is ready!"
echo "  Open your browser and go to:"
echo "  http://localhost:8501"
echo "============================================"
echo ""
exec streamlit run web/app.py --server.port=8501 --server.address=0.0.0.0
