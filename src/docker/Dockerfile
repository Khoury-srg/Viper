# This Dockerfile
FROM dorowu/ubuntu-desktop-lxde-vnc:focal

ENV PYTHONUNBUFFERED True

# https://www.omgubuntu.co.uk/2017/08/fix-google-gpg-key-linux-repository-error
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

WORKDIR /
RUN wget https://sh.rustup.rs -O sh.rustup.rs && sh sh.rustup.rs -y
RUN wget https://raw.githubusercontent.com/technomancy/leiningen/stable/bin/lein && chmod u+x lein
ENV PATH "$PATH:$HOME/.cargo/bin:/"

COPY ./resources/ /
COPY ./viper_backend/viper/docker/ /

Run apt-get update && apt-get install -y libgmp-dev cmake g++ zlib1g-dev openjdk-11-jdk libclang-dev

# install lein and build elle
WORKDIR /elle-cli-0.1.3
RUN lein deps && lein uberjar

# 
WORKDIR /dbcop
RUN cargo build

WORKDIR /BE19_translator
RUN cargo build

# deps
RUN apt-get install -y python3.8 python3-setuptools python3-pip

# monosat
WORKDIR /monosat
RUN cmake -DPYTHON=ON . && \
    make -j8 && \
    make install

# z3
WORKDIR /z3
RUN python scripts/mk_make.py
WORKDIR build
RUN make -j8 && \
    make install


# python pkgs
WORKDIR /
RUN pip3 install --no-cache-dir -r requirements.txt

ENV VIPER_HOME /CobraPlus