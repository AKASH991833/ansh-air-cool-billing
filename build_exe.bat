@echo off
setlocal
echo Building AC Billing System standalone EXE...
echo.
python build.py
echo.
if exist "dist\AC_Billing_System.exe" (
    echo SUCCESS! EXE created at: dist\AC_Billing_System.exe
    where ISCC.exe >nul 2>&1
    if %errorlevel%==0 (
        echo Creating Windows installer...
        ISCC.exe installer.iss
        if exist "installer-output\AnshAirCoolBilling-Setup-1.0.0.exe" (
            echo SUCCESS! Installer created in installer-output\
        ) else (
            echo WARNING: EXE built, but installer creation failed.
        )
    ) else (
        echo NOTE: Inno Setup not found. EXE is ready; install Inno Setup to create a setup installer.
    )
) else (
    echo ERROR: Build failed
    exit /b 1
)
endlocal
