@echo off
echo ========================================
echo AI-Based Smart Grievance System
echo ========================================
echo.
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Flask application...
echo.
echo Application will be available at:
echo http://127.0.0.1:5000
echo.
echo Demo Credentials:
echo Student: john@student.com / student123
echo Faculty: robert@faculty.com / faculty123
echo.
python app.py
pause
