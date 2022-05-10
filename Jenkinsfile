pipeline {
    agent {
        kubernetes {
            cloud 'openshift'
            yaml """
apiVersion: v1
kind: Pod
metadata:
    labels:
        jenkins-build-id: ${env.BUILD_ID}
spec:
    serviceaccount: jenkins
    containers:
    - name: vcs-argocd-cleanup
      # image: images.paas.redhat.com/rhvcs/vcs-argocd-cleanup
      image: quay.io/kharyam/vcs-argocd-cleanup:latest
      imagePullPolicy: Always
      resources:
        limits:
            cpu: 500m
            memory: 512Mi
        requests:
            cpu: 500m
            memory: 512Mi
      tty: true
      volumeMounts:
      - name: pgp-secret
        mountPath: "/config/pgp-private-keys"
        readOnly: true
      - name: ploigos-config
        mountPath: "/config/plogos-config"
        readOnly: true
      - name: ploigos-config-secrets
        mountPath: "/config/ploigos-config-secrets"
        readOnly: true
    volumes:
      - name: pgp-secret
        secret:
          secretName: jenkins-pgp-private-key
      - name: ploigos-config
        secret:
          secretName: ploigos-platform-config
      - name: ploigos-config-secrets
        secret:
          secretName: ploigos-platform-config-secrets
"""
        }
    }
    stages {
        stage('Cleanup ArgoCD DEV Project') {
            environment {
                REFQUARKUS_GIT_CREDS   = credentials('vcs-jenkins-reference-quarkus-mvn')
                BACKEND_GIT_CREDS      = credentials('vcs-jenkins-reference-quarkus-mvn')
                FRONTEND_GIT_CREDS     = credentials('vcs-jenkins-reference-quarkus-mvn')
                AUTOAPPROVAL_GIT_CREDS = credentials('vcs-jenkins-reference-quarkus-mvn')
                SERVERPAGES_GIT_CREDS  = credentials('vcs-jenkins-reference-quarkus-mvn')
            }
            steps {
                container("vcs-argocd-cleanup") {
                    script {
                        sh '''
                            gpg --import $CONFIG_DIR/pgp-private-keys/jenkins.key
                            export CONFIG_FILE=$CONFIG_DIR/config.yaml
                            export ARGOCD_USERNAME=$(cat $CONFIG_DIR/ploigos-config/ploigos-platform-config.yml  | yq r - 'step-runner-config.deploy.*.config.argocd-username')
                            export ARGOCD_SERVER=$(cat $CONFIG_DIR/ploigos-config/ploigos-platform-config.yml  | yq r - 'step-runner-config.deploy.*.config.argocd-api')
                            export ARGOCD_PASSWORD=$(sops -d $CONFIG_DIR/ploigos-config-secrets/ploigos-platform-config-secrets.yml  | yq r - 'step-runner-config.deploy.*.config.argocd-password')
                            /app/argocd-cleanup.py                            
                        '''
                    }
                }
            }
        }
    }
}
