FROM gradle:9.4.1-jdk21

# 1. 기본 패키지 및 환경 설정
USER root
ENV PATH="/usr/local/bin:${PATH}"

RUN apt-get update && apt-get install -y \
    curl \
    git \
    iputils-ping \
    netcat-openbsd \
    nodejs \
    npm \
    unzip \
    vim   \
    buildah \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://dlcdn.apache.org/maven/maven-3/3.9.14/binaries/apache-maven-3.9.14-bin.tar.gz| tar -xzC /usr/local \
    && ln -s /usr/local/apache-maven-3.9.14/bin/mvn /usr/local/bin/mvn

RUN curl -fsSL https://github.com/containerd/nerdctl/releases/download/v2.2.1/nerdctl-full-2.2.1-linux-amd64.tar.gz | tar -xzC /usr/local

RUN curl -fsSL https://github.com/starship/starship/releases/download/v1.24.2/starship-x86_64-unknown-linux-gnu.tar.gz | tar -xzC /usr/local/bin && echo 'eval "$(starship init bash)"' >> ~/.bashrc

RUN curl -fsSL  https://github.com/derailed/k9s/releases/download/v0.50.18/k9s_Linux_amd64.tar.gz | tar -xzC /usr/local/bin

RUN curl -fsSL https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2Fv5.8.1/kustomize_v5.8.1_linux_amd64.tar.gz | tar -xzC /usr/local/bin

# 최종 확인용
RUN mvn -version && nerdctl --version && starship --version && k9s version && kustomize version

CMD ["bash"]
