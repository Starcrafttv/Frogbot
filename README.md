# Frogbot
 

# Docker:
 Build = 'docker build -t frogbot .'
 Run = 'docker run --rm --name frogbot -v /root/projects/Frogbot/bot:/app/bot frogbot'

 # Usefull Docker Commands:
- List of running containers 'docker ps' (-a including stopped containers)
- kill all running containers with 'docker kill $(docker ps -q)'
- delete all stopped containers with 'docker rm $(docker ps -a -q)'
- delete all images with 'docker rmi $(docker images -q)'
- update and stop a container that is in a crash-loop with 'docker update --restart=no && docker stop'

# Screen:
Start: 'screen -S frogbot'
Reattach: 'screen -r frogbot'
Detach: Ctrl+a d
Rename current screen: Ctrl+a A
Kill screen: Ctrl+a k




