# VoIP Phone System using FreeSWITCH

## 1. Overview

This project implements a complete SIP-based VoIP phone system based on FreeSWITCH, as outlined in the VoIP Engineer assignment. It includes a FreeSWITCH media server, two SIP clients, and an ESL (Event Socket Library) client for real-time call event logging. The entire system is containerized using Docker and Docker Compose for easy deployment and scalability.

---

## 2. Project Components

* **SIP/Media Server**: **FreeSWITCH** is used as the core of the system, acting as a SIP registrar, proxy, and media server.
* **SIP Clients**: Any standard SIP client (e.g., Zoiper, Linphone) can be used to register as users **1000** or **1001**.
* **ESL Client**: A **Python** script connects to FreeSWITCH's Event Socket to monitor and log call events in real-time.

---

## 3. Features Implemented

### Basic Requirements
- [x] SIP clients can successfully register, make, and receive calls between each other.
- [x] An ESL client logs the start, answer, and end timestamps of every call to a log file (`logs/call_log.txt`).

### Bonus Requirements
- [x] **Authentication**: SIP clients must authenticate with a username and password before registering.
- [x] **NAT Traversal**: The FreeSWITCH configuration is set up to handle clients behind NAT.
- [x] **Dockerization**: The entire project, including the FreeSWITCH server and the ESL logger script, is containerized using Docker and `docker-compose`.

---

## 4. Project Setup and Configuration

### Prerequisites
* [Docker](https://www.docker.com/get-started)
* [Docker Compose](https://docs.docker.com/compose/install/)
* A softphone (SIP client) like [Zoiper](https://www.zoiper.com/) or [Linphone](https://www.linphone.org/).

### Directory Structure
Create the following directory and file structure for the project:

```
.
├── docker-compose.yml
├── Dockerfile
├── freeswitch_conf/
│   ├── dialplan/
│   │   └── default.xml
│   └── sip_profiles/
│       └── internal.xml
│   └── directory/
│       └── default/
│           ├── 1000.xml
│           └── 1001.xml
├── esl_script/
│   ├── esl_call_logger.py
│   └── requirements.txt
└── logs/
    └── .gitkeep  (The logs directory will be created here)
```

### Step 1: Create FreeSWITCH Configuration Files

These files configure users, NAT settings, and the dialplan.

**A) NAT & SIP Profile (`freeswitch_conf/sip_profiles/internal.xml`)**
This profile tells FreeSWITCH how to handle clients behind a NAT router.

```xml
<profile name="internal">
  <param name="ext-rtp-ip" value="auto-nat"/>
  <param name="ext-sip-ip" value="auto-nat"/>

  <gateways>
  </gateways>

  <aliases>
  </aliases>

  <domains>
    <domain name="all" alias="true" parse="false"/>
  </domains>

  <settings>
    <param name="auth-calls" value="true"/>
    <param name="auth-all-packets" value="false"/>
    <param name="rfc2833-pt" value="101"/>
    <param name="sip-port" value="5060"/>
    <param name="dialplan" value="XML"/>
    <param name="context" value="default"/>
    <param name="dtmf-duration" value="100"/>
    <param name="inbound-codec-prefs" value="$${global_codec_prefs}"/>
    <param name="outbound-codec-prefs" value="$${global_codec_prefs}"/>
    <param name="hold-music" value="$${moh_uri}"/>
  </settings>
</profile>
```

**B) User 1000 (`freeswitch_conf/directory/default/1000.xml`)**

```xml
<include>
  <user id="1000">
    <params>
      <param name="password" value="1234"/>
      <param name="vm-password" value="1000"/>
    </params>
    <variables>
      <variable name="toll_allow" value="domestic,international,local"/>
      <variable name="accountcode" value="1000"/>
      <variable name="user_context" value="default"/>
    </variables>
  </user>
</include>
```

**C) User 1001 (`freeswitch_conf/directory/default/1001.xml`)**

```xml
<include>
  <user id="1001">
    <params>
      <param name="password" value="1234"/>
      <param name="vm-password" value="1001"/>
    </params>
    <variables>
      <variable name="toll_allow" value="domestic,international,local"/>
      <variable name="accountcode" value="1001"/>
      <variable name="user_context" value="default"/>
    </variables>
  </user>
</include>
```

**D) Dialplan (`freeswitch_conf/dialplan/default.xml`)**
This simple dialplan allows users in the `default` context to call each other.

```xml
<include>
  <context name="default">
    <extension name="Local_Extension">
      <condition field="destination_number" expression="^(10[01][0-9])$">
        <action application="bridge" data="user/${destination_number}"/>
      </condition>
    </extension>
  </context>
</include>
```

### Step 2: Create the ESL Logger Script

**A) Python Dependencies (`esl_script/requirements.txt`)**

```
esl==0.8
```

**B) ESL Script (`esl_script/esl_call_logger.py`)**
*This is the Python code you requested. See the separate code block below this README.*

### Step 3: Create Docker Files

**A) Dockerfile (`Dockerfile`)**
*This is the `Dockerfile` we developed previously, updated to copy your new configuration files.*

```dockerfile
# Stage 1: The Builder
FROM ubuntu:22.04 AS builder
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    build-essential git autoconf automake libtool wget cmake nasm \
    libjpeg-dev libpcre3-dev libspeex-dev libspeexdsp-dev libsqlite3-dev \
    libcurl4-openssl-dev libopus-dev libsndfile1-dev libavformat-dev \
    libswscale-dev liblua5.2-dev uuid-dev libsofia-sip-ua-dev \
    libspandsp-dev libks-dev libldns-dev libedit-dev \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /usr/src
RUN git clone [https://github.com/signalwire/freeswitch.git](https://github.com/signalwire/freeswitch.git) -b v1.10
WORKDIR /usr/src/freeswitch
COPY ./freeswitch_conf/ /tmp/custom_conf/
RUN ./bootstrap.sh -j && ./configure && make -j$(nproc) && make install
RUN cp -r /tmp/custom_conf/* /usr/local/freeswitch/conf/

# Stage 2: The Runtime Image
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    libspeex1 libspeexdsp1 libopus0 liblua5.2-0 libsndfile1 \
    libsqlite3-0 libsofia-sip-ua0 libspandsp2 libcurl4 \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*
RUN groupadd --gid 1000 freeswitch && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home freeswitch
COPY --from=builder /usr/local/freeswitch /usr/local/freeswitch
RUN chown -R freeswitch:freeswitch /usr/local/freeswitch
USER freeswitch
EXPOSE 5060/udp 5060/tcp 5080/tcp 8021/tcp 16384-32768/udp
CMD ["/usr/local/freeswitch/bin/freeswitch", "-nc", "-nonat"]
```

**B) Docker Compose (`docker-compose.yml`)**
This file orchestrates both the FreeSWITCH and the ESL logger containers.

```yaml
version: '3.7'

services:
  freeswitch:
    build: .
    image: my-freeswitch
    container_name: freeswitch
    ports:
      - "5060:5060/udp"
      - "5060:5060/tcp"
      - "5080:5080/tcp"
      - "8021:8021/tcp" # ESL Port
      - "16384-32768:16384-32768/udp" # RTP Ports
    volumes:
      - ./freeswitch_conf:/usr/local/freeswitch/conf
    restart: unless-stopped

  esl_logger:
    image: python:3.9-slim
    container_name: esl_logger
    command: python esl_call_logger.py
    volumes:
      - ./esl_script:/app
      - ./logs:/app/logs
    working_dir: /app
    environment:
      - FS_HOST=freeswitch
      - FS_PORT=8021
      - FS_PASSWORD=ClueCon
    depends_on:
      - freeswitch
    restart: unless-stopped
    entrypoint: >
      sh -c "
        pip install -r requirements.txt &&
        python esl_call_logger.py
      "
```

### Step 4: Run the System

With all the files in place, start the entire system with one command:

```bash
docker-compose up -d
```

### Step 5: Configure SIP Clients

Configure two instances of your softphone (e.g., Zoiper) with the following details. Use your computer's local IP address or the public IP if deployed on the cloud.

**Client A:**
* **Domain/Server:** `<Your_Server_IP>`
* **Username:** `1000`
* **Password:** `1234`

**Client B:**
* **Domain/Server:** `<Your_Server_IP>`
* **Username:** `1001`
* **Password:** `1234`

---

## 5. Demonstration

1.  Register both SIP clients. They should connect successfully.
2.  From Client A (user 1000), dial `1001`.
3.  Client B (user 1001) should ring. Answer the call.
4.  Speak for a few seconds, then hang up.
5.  Check the log file `logs/call_log.txt` on your host machine. It will contain the start, answer, and end timestamps for the call.

    Example `call_log.txt` output:
    ```
    2025-07-21 02:30:15 - INFO: Call Initiated: a1b2c3d4-e5f6-7890-1234-567890abcdef | From: 1000 | To: 1001
    2025-07-21 02:30:20 - INFO: Call Answered: a1b2c3d4-e5f6-7890-1234-567890abcdef
    2025-07-21 02:30:45 - INFO: Call Ended: a1b2c3d4-e5f6-7890-1234-567890abcdef
    ```

---

## 6. Cloud Deployment

This Docker-based setup is ready for the cloud. The steps are:

1.  **Provision a Cloud Server:** Get a virtual machine from any provider (AWS EC2, DigitalOcean, etc.). Ensure its security group or firewall allows traffic on the ports defined in `docker-compose.yml`.
2.  **Install Docker:** Install Docker and Docker Compose on the server.
3.  **Clone Repository:** Clone your project repository onto the server.
4.  **Update NAT Configuration:** **This is the most important step.** Edit `freeswitch_conf/sip_profiles/internal.xml` and replace `auto-nat` with the server's **public IP address**:
    ```xml
    <param name="ext-rtp-ip" value="YOUR_PUBLIC_IP_HERE"/>
    <param name="ext-sip-ip" value="YOUR_PUBLIC_IP_HERE"/>
    ```
5.  **Launch:** Run `docker-compose up -d` in the project directory on the server.
6.  **Configure Clients:** Point your SIP clients to the server's public IP address.
