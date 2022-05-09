FROM quay.io/ploigos/ploigos-tool-argocd

USER 0
ENV CONFIG_DIR=/config
VOLUME /config

RUN dnf update -y ; mkdir /app 
ADD argocd-cleanup.py cleanup.sh /app
ADD config.yaml /config
RUN chmod 550 -R /app && chgrp 0 -R /app && pip install git-python sh pyyaml

VOLUME /config
USER 1001

