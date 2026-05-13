@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Building executable...
pyinstaller demo_game.spec

echo Build complete! Check the 'dist/DemoGame' folder for your game.
pause