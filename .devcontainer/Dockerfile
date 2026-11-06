# Superset of the home-web-apps, home-playbooks and home-kubernetes devcontainers.
FROM mcr.microsoft.com/devcontainers/base:jammy

# System dependencies (union of all three repos)
RUN apt-get update \
	&& apt-get install -y \
	curl \
	dnsutils \
	expect \
	ffmpeg \
	git \
	golang \
	jq \
	libcairo-gobject2 \
	libgdk-pixbuf-2.0-0 \
	libgtk-3-0 \
	libpangocairo-1.0-0 \
	libxcursor1 \
	python3 \
	python3-pip \
	python3-venv \
	ripgrep \
	smbclient \
	sshpass \
	sudo \
	vim \
	wget \
	zsh \
	&& rm -rf /var/lib/apt/lists/*

# yq (pinned to the version home-kubernetes uses; home-web-apps used "latest")
ARG YQ_VERSION=v4.44.1
RUN wget -T 30 --tries=3 -q "https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/yq_linux_amd64" -O /usr/local/bin/yq \
	&& chmod +x /usr/local/bin/yq

USER vscode

# Ansible tooling (from home-playbooks)
RUN pip3 install \
    ansible \
    paramiko \
    pyopenssl \
    pywinrm \
    pre-commit \
    ansible-lint
