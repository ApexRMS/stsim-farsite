if "%SSIM_FARSITE_MODULE_BATCH_FILE_LOCATION%" == "" (
	echo Please define the Environmental Variable 'SSIM_FARSITE_MODULE_BATCH_FILE_LOCATION' in the Farsite Library Properties 1>&2
	exit /b -1
)
call "%SSIM_FARSITE_MODULE_BATCH_FILE_LOCATION%\o4w_env.bat"
cd /d %~dp0
StartProcess --name=python.exe --no-error-box --args="farsite.py" >> "farsite.bat.log" 2>&1
if %ERRORLEVEL% == -1073741819 (
	exit /b 0
) else (
	ECHO There was error during the running of the Farsite python script. For details check the run log at "%~dp0farsite.bat.log" 1>&2
	exit /b %ERRORLEVEL%
)