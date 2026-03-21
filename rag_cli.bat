@echo off
echo 🤖 RAG Management CLI for Assaf's Agent
echo.

REM Check if backend is running
curl -s http://localhost:8000/ >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Backend is not running. Please start it first:
    echo    uvicorn app.main:app --host 0.0.0.0 --port 8000
    pause
    exit /b 1
)

if "%~1"=="" (
    echo Usage:
    echo   rag_cli.bat stats          - Show RAG system statistics
    echo   rag_cli.bat test           - Test search performance
    echo   rag_cli.bat gaps           - Analyze knowledge gaps
    echo   rag_cli.bat optimize        - Optimize search thresholds
    echo   rag_cli.bat rebuild         - Rebuild RAG index
    echo   rag_cli.bat export          - Export knowledge summary
    echo.
    echo Examples:
    echo   rag_cli.bat stats
    echo   rag_cli.bat test --queries "skills" "experience"
    echo   rag_cli.bat gaps --topics "technical" "personal"
    pause
    exit /b 0
)

REM Run the RAG CLI
python rag_cli.py %*

echo.
echo ✅ RAG command completed!
pause
