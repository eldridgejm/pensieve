FROM debian:latest
RUN apt-get update && apt-get install -y\
    wget\
    build-essential\
    openssl\
    python3\
    python3-venv\
    openssh-server\
    git\
    libssl-dev
WORKDIR /root
RUN useradd tester -m -s /bin/bash
RUN echo tester:testing | chpasswd
USER tester
WORKDIR /home/tester
ADD id_rsa.pub .ssh/authorized_keys
# install the repo agent
RUN git clone https://github.com/eldridgejm/pensieve-agent
RUN wget https://github.com/eldridgejm/pensieve-agent/archive/bcc550ae1c7fcdd709ab72f70d2cf6e941cd39b5.tar.gz -O pensieve-agent.tar.gz &&\
    tar xvf pensieve-agent.tar.gz
RUN python3 -m venv env
RUN ./env/bin/pip install wheel
RUN ./env/bin/pip install ./pensieve-agent
RUN mkdir pensieve
RUN echo "export PATH=/home/tester/env/bin:$PATH" >> ~/.bashrc
USER root
# create privilege separation directory
RUN mkdir /run/sshd
ADD initialize_repositories.sh .
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
