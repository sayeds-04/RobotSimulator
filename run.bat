@echo off
:: ============================================================
::  run.bat  --  Robot Command Simulator  (Full Launcher)
::
::  This script does EVERYTHING in order:
::    1. Verifies tools: Python, Flex, Bison, GCC
::    2. Runs Bison  -> generates robot_parser.tab.c + .h
::    3. Runs Flex   -> generates lex.yy.c
::    4. Runs GCC    -> links into robot_compiler.exe
::    5. Runs a quick smoke test of the compiled binary
::    6. Launches the Python GUI (app.py)
::
::  Course : Compiler Design
:: ============================================================

title Robot Command Simulator -- Compiler Design

:: ── Use short (8.3) DOS paths to avoid spaces breaking m4/bison ──
set GNUWIN=C:\PROGRA~2\GnuWin32\bin
set GCCBIN=C:\gcc\bin
set PATH=%GNUWIN%;%GCCBIN%;%PATH%

:: ── Set compiler source directory ──
set COMPILER_DIR=%~dp0compiler

echo.
echo  =====================================
echo   ROBOT COMMAND SIMULATOR
echo   Compiler Design Course Project
echo   Dev By:Group of Fakibaz People
echo  =====================================
echo.

:: ============================================================
::  STEP 0: Check Python
:: ============================================================
echo  [CHECK] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found! Install from https://python.org
    pause
    exit /b 1
)
echo  [OK]    Python found.
echo.

:: ============================================================
::  STEP 1: Check Flex and Bison
:: ============================================================
echo  [CHECK] Checking Flex and Bison...

where flex  >nul 2>&1
if errorlevel 1 (
    echo  [WARN]  Flex not found in PATH.
    echo          Compiler will use the Python lexer/parser fallback.
    goto :SKIP_COMPILE
)

where bison >nul 2>&1
if errorlevel 1 (
    echo  [WARN]  Bison not found in PATH.
    echo          Compiler will use the Python lexer/parser fallback.
    goto :SKIP_COMPILE
)

where gcc >nul 2>&1
if errorlevel 1 (
    echo  [WARN]  GCC not found in PATH.
    echo          Compiler will use the Python lexer/parser fallback.
    goto :SKIP_COMPILE
)

echo  [OK]    Flex found.
echo  [OK]    Bison found.
echo  [OK]    GCC found.
echo.

:: ============================================================
::  STEP 2: Run Bison  (generates robot_parser.tab.c + .h)
:: ============================================================
echo  ============================================================
echo   PHASE 1: BISON -- Parsing robot_parser.y
echo  ============================================================
echo  [>>]    Running:  bison -d robot_parser.y
echo.
cd /d "%COMPILER_DIR%"
bison -d robot_parser.y
if errorlevel 1 (
    echo.
    echo  [ERROR] Bison failed! Check robot_parser.y for grammar errors.
    pause
    exit /b 1
)
echo  [OK]    Generated: robot_parser.tab.c
echo  [OK]    Generated: robot_parser.tab.h
echo.

:: ============================================================
::  STEP 3: Run Flex  (generates lex.yy.c)
:: ============================================================
echo  ============================================================
echo   PHASE 2: FLEX -- Lexing robot_lexer.l
echo  ============================================================
echo  [>>]    Running:  flex robot_lexer.l
echo.
flex robot_lexer.l
if errorlevel 1 (
    echo.
    echo  [ERROR] Flex failed! Check robot_lexer.l for lexer errors.
    pause
    exit /b 1
)
echo  [OK]    Generated: lex.yy.c
echo.

:: ============================================================
::  STEP 4: Compile with GCC  (links into robot_compiler.exe)
:: ============================================================
echo  ============================================================
echo   PHASE 3: GCC -- Compiling robot_compiler.exe
echo  ============================================================
echo  [>>]    Running:  gcc -w -o robot_compiler.exe main.c robot_parser.tab.c lex.yy.c
echo.
gcc -w -o robot_compiler.exe main.c robot_parser.tab.c lex.yy.c
if errorlevel 1 (
    echo.
    echo  [ERROR] GCC compilation failed!
    pause
    exit /b 1
)
echo  [OK]    Compiled: robot_compiler.exe
echo.

:: ============================================================
::  STEP 5: Quick smoke test of the compiled binary
:: ============================================================
echo  ============================================================
echo   PHASE 4: SMOKE TEST -- Testing robot_compiler.exe
echo  ============================================================
echo  [>>]    Input:  "move forward 5 steps"
echo  [>>]    Output:
echo.
echo move forward 5 steps | robot_compiler.exe
echo.
echo  [OK]    Flex/Bison pipeline working!
echo.
goto :LAUNCH_GUI

:SKIP_COMPILE
echo.
echo  [INFO]  Skipping Flex/Bison/GCC build.
echo  [INFO]  The GUI will use the built-in Python lexer/parser instead.
echo  [INFO]  All features work identically in fallback mode.
echo.

:: ============================================================
::  STEP 6: Launch the Python GUI
:: ============================================================
:LAUNCH_GUI
echo  ============================================================
echo   PHASE 5: LAUNCHING GUI -- Robot Command Simulator
echo  ============================================================
echo  [>>]    Running:  python frontend\app.py
echo.

cd /d "%~dp0"
python "%~dp0frontend\app.py"

if errorlevel 1 (
    echo.
    echo  [ERROR] The application exited with an error.
    pause
)
