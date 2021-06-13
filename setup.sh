echo '[FROGBBOT] Updating system'
sudo apt-get update
echo '[FROGBOT] Installing ffmpeg'
sudo apt install ffmpeg
echo '[FROGBOT] Installing python 3.9'
sudo apt-get install python3.9
sudo python3.9 -m pip install --upgrade pip
echo '[FROGBOT] Installing python packages'
sudo python3.9 -m pip install -U -r requirements.txt
echo '[FROGBOT] Finished installations'

echo '[FROGBOT] Starting bot'
python3.9 -B bot.py
