FROM quay.io/ploigos/ploigos-tool-argocd

ARG PLOIGOS_USER_UID

USER 0
ENV CONFIG_DIR=/config
VOLUME /config

RUN dnf update -y ; mkdir /app 
ADD argocd-cleanup.py /app
ADD config.yaml /config
RUN chmod 550 -R /app && chgrp 0 -R /app && pip install git-python sh pyyaml

VOLUME /config
USER ${PLOIGOS_USER_UID}
