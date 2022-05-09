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
        name: ploigos-platform-config-secrets
      - mountPath: /config/ploigos-platform-config.yml
        name: ploigos-platform-config
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
                BACKEND_GIT_CREDS      = credentials('vcs-jenkins-reference-quarkus-mvn')
                FRONTEND_GIT_CREDS     = credentials('vcs-jenkins-reference-quarkus-mvn')
                AUTOAPPROVAL_GIT_CREDS = credentials('vcs-jenkins-reference-quarkus-mvn')
                SERVERPAGES_GIT_CREDS  = credentials('vcs-jenkins-reference-quarkus-mvn')
            }
            steps {
                container("vcs-argocd-cleanup") {
                    script {
                        sh '''
                            /app/cleanup.sh
                        '''
                    }
                }
            }
        }
    }
}
