#!/bin/bash
gpg --import $CONFIG_DIR/jenkins.key
export CONFIG_FILE=$CONFIG_DIR/config.yaml
export ARGOCD_USERNAME=$(cat $CONFIG_DIR/ploigos-platform-config.yml  | yq r - 'step-runner-config.deploy.*.config.argocd-username')
export ARGOCD_SERVER=$(cat $CONFIG_DIR/ploigos-platform-config.yml  | yq r - 'step-runner-config.deploy.*.config.argocd-api')
export ARGOCD_PASSWORD=$(sops -d $CONFIG_DIR/ploigos-platform-config-secrets.yml  | yq r - 'step-runner-config.deploy.*.config.argocd-password')
/app/argocd-cleanup.py
