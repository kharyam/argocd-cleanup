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
        - mountPath: /config/ploigos-platform-config-secrets.yml
          name: ploigos-platform-config-secrets.yml
        - mountPath: /config/ploigos-platform-config.yml
          name: ploigos-platform-config.yml
    volumes:
    - name: ploigos-platform-config-secrets
      secret:
        secretName: ploigos-platform-config-secrets
    - name: ploigos-platform-config
      secret:
        secretName: ploigos-platform-config
"""
        }
    }
    stages {
        stage('Cleanup ArgoCD DEV Project') {
            environment {
                REFQUARKUS_GIT_CREDS   = credentials('vcs-jenkins-reference-quarkus-mvn')
                BACKEND_GIT_CREDS      = credentials('vcs-jenkins-backend-monorepo')
                FRONTEND_GIT_CREDS     = credentials('vcs-jenkins-frontend')
                AUTOAPPROVAL_GIT_CREDS = credentials('vcs-jenkins-auto-approval')
                SERVERPAGES_GIT_CREDS  = credentials('vcs-jenkins-server-pages')
            }
            steps {
                container(vcs-argocd-cleanup) {
                    script {
                        sh """
                        /app/cleanup.sh
                        """
                    }
                }
            }
        }
    }
}
