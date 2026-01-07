FROM ubuntu:22.04

ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=$USER_UID

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    build-essential cmake git libboost-all-dev libsdl2-dev \
    libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libfreeimage-dev \
    libfreetype6-dev libcurl4-openssl-dev libasound2-dev \
    mesa-utils xorg openbox python3-pip imagemagick vlc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
    sudo bash-completion vim apt-utils git wget xz-utils \
    libsdl2-dev libsdl2-mixer-dev libfreeimage-dev libfreetype6-dev \
    libcurl4-openssl-dev rapidjson-dev libasound2-dev libgl1-mesa-dev build-essential \
    libboost-all-dev cmake fonts-droid-fallback libvlc-dev libvlccore-dev vlc-bin libint-dev \
    gettext locales-all unzip && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN HASH="5d643bfcf6327718d3ccc6c7676e57cb70e0203c" && \
    cd /opt && \
    git clone --recursive https://github.com/batocera-linux/batocera-emulationstation && \
    cd batocera-emulationstation && \
    git checkout $HASH && \
    cmake -DSCREENSCRAPER_DEV_LOGIN="devid=jelos&devpassword=jelos" . && \
    make && \
    make install

RUN mkdir -p /opt/roms && \
    chown $USER_UID:$USER_GID /opt/roms

RUN mkdir -p /opt/userdata && \
    chown $USER_UID:$USER_GID /opt/userdata

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/bash-history/.bash_history" \
    && mkdir /bash-history \
    && touch /bash-history/.bash_history \
    && chown -R $USERNAME /bash-history \
    && echo "$SNIPPET" >> "/home/$USERNAME/.bashrc"

USER $USERNAME

CMD ["/bin/bash"]
