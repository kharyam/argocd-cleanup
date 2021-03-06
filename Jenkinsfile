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
        mountPath: "/config/jenkins.key"
        subPath: "jenkins.key"
        readOnly: true
      - name: ploigos-config
        mountPath: "/config/ploigos-platform-config.yml"
        subPath: "ploigos-platform-config.yml"
        readOnly: true
      - name: ploigos-config-secrets
        mountPath: "/config/ploigos-platform-config-secrets.yml"
        subPath: "ploigos-platform-config-secrets.yml"
        readOnly: true
    volumes:
      - name: pgp-secret
        secret:
          secretName: jenkins-pgp-private-key
      - name: ploigos-config
        configMap:
          name: ploigos-platform-config
      - name: ploigos-config-secrets
        secret:
          secretName: ploigos-platform-config-secrets
"""
        }
    }
    stages {
        stage('Cleanup ArgoCD DEV Projects') {
            environment {
                REFQUARKUS_GIT_CREDS   = credentials('vcs-jenkins-reference-quarkus-mvn')
                BACKEND_GIT_CREDS      = credentials('vcs-jenkins-backend-monorepo')
                FRONTEND_GIT_CREDS     = credentials('vcs-jenkins-frontend')
                AUTOAPPROVAL_GIT_CREDS = credentials('vcs-jenkins-auto-approval')
                SERVERPAGES_GIT_CREDS  = credentials('vcs-jenkins-server-pages')
            }
            steps {
                container("vcs-argocd-cleanup") {
                    script {
                        sh '''
                            set +x
                            gpg --import $CONFIG_DIR/jenkins.key
                            export CONFIG_FILE=$CONFIG_DIR/config.yaml
                            export ARGOCD_USERNAME=$(cat $CONFIG_DIR/ploigos-platform-config.yml  | yq r - 'step-runner-config.deploy.*.config.argocd-username')
                            export ARGOCD_SERVER=$(cat $CONFIG_DIR/ploigos-platform-config.yml  | yq r - 'step-runner-config.deploy.*.config.argocd-api')
                            export ARGOCD_PASSWORD=$(sops -d $CONFIG_DIR/ploigos-platform-config-secrets.yml  | yq r - 'step-runner-config.deploy.*.config.argocd-password')
                            /app/argocd-cleanup.py                            
                        '''
                    }
                }
            }
        }
    }
}
