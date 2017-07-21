# discloud
The weather on your discord server.

# Setup
## Linux
1. Install Git
    - Debian : `sudo apt-get install git-all`
    - Fedora : `sudo dnf install git-all`
2. Clone the Git repository
    - `sudo git clone github.com/mbouchenoire/discloud.git /etc`
3. Configure the bot
    - create the file `config/application.ini` using [`config/application_example.ini`](config/application_example.ini) as a reference
4. Run the bot
    - using Python 3 on Debian 8+ :
        1. `cd /etc/discloud`
        2. install `pip` : `sudo apt-get install -y python3-pip`
        3. `sudo pip3 install -r requirements.txt`
        4. `sudo python3 discloud/__ini__.py &`
    - using Docker :
        1. [install Docker](https://docs.docker.com/engine/installation/)
        3. `cd /etc/discloud`
        2. if the bot is ***not*** running on an ARM architecture (e.g. Raspberry PI), replace `FROM arm32v7/python:3` by `FROM python:3` in the `Dockerfile`
        3. build the Docker image : `sudo docker build -t discloud .`
        4. run the Docker container : `sudo docker run -dit discloud`