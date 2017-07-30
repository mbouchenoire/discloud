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
        2. `cd /etc/discloud`
        3. build the Docker image :
           - on a standard x86 architecture : `sudo docker build -t discloud .`
           - on an ARM architecture : `sudo docker build -t discloud -f Dockerfile.arm`
        4. run the Docker container : `sudo docker run -dit discloud`