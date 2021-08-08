echo '[FROGBBOT] Updating system'
sudo apt-get update
echo '[FROGBOT] Installing ffmpeg'
sudo apt install ffmpeg
echo '[FROGBOT] Installing the python 3.9 enviroment'
sudo apt-get install python3.9-venv

echo '[FROGBOT] Starting virtual enviroment'
python3.9 -m venv env
source env/bin/activate
pip3 install --upgrade pip
echo '[FROGBOT] Installing python packages'
python3 -m pip install -r requirements.txt
echo '[FROGBOT] Finished installations'

echo '[FROGBOT] Starting bot'
python3 -B main.py
