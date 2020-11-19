TIRA 9 Web
======
  - [Local Deployment](#local-deployment)
  - [K8s Deployment](#k8s-deployment)
  - [Model Integration](#model-integration)
  

Local Deployment
----------------

To start the frontend server, run:
  
    ~# make run-tira-docker
  
You can access the frontend at `http://localhost:8080` with User='user' and Password='password'
  
#### Open Issues:
Add remote debugging capabilities to Tomcat by adding this to the enviromment:
 
    JAVA_OPTS="${JAVA_OPTS} -Xdebug -Xrunjdwp:transport=dt_socket,address=8000,server=y,suspend=n"


K8s Deployment
----------------

Preparation:
- Create and install a dedicated ssh-key for the tira-web-server
    - You can skip this if the ssh-key is already known by kubernetes, i.e. this secret exists:
      
        ```kubectl get secrets tira-webis18-ssh-key```
    
    - Execute the following commands:
 
      ```
      ~$ ssh-keygen -q -N "" -f tmp-tira-ssh-key  
      ~$ kubectl create secret generic tira-webis18-ssh-key --from-file=id_rsa=tmp-tira-ssh-key
      ```
      
    - Add the content of tmp-tira-ssh-key.pub to the associated tira-pub-key-webis16 section of https://git.webis.de/code-generic/code-saltstack/blob/master/src/srv/salt/states/tira/init.sls and apply the tira state to all associated nodes with salt
        
- Tira must be installed on every node in the kubernetes cluster
  - You can skip this step on our kubernetes-cluster, since tira is installed on all nodes with salt
  - Additionally, this step gets obsolete as soon as all tira scripts are embedded in the docker image.)
  
Deploy to Kubernetes:
 
    make k8s-deploy
  
### Open Issues:
- Install tira-scripts as git-submodule in lib and check it out during build to remove the necessarity to mount tira scripts
- Ask Martin if its necessary to have VBoxManage in the Webserver or if it is fine to have the dummy-script
- Rename SSH-Secret
- Move everything to the webisservice namespace

### Debugging k8s deployment

Connect to the tira frontend pod:
- Use kubectl with betaweb context
    
      kubectl config use betaweb
    
- Determine the name of the pod
    
      kubectl get all
    
- Connect to the pod (assuming its name is pod/tira-web-client-66f7c54fd7-qc95v):
    
      kubectl exec -ti pod/tira-web-client-66f7c54fd7-qc95v /bin/bash
    
You can also forward ports to the tira frontend pod: 
 - https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands
  

Model Integration
-----------

To carry out development against the real data (you can mount this into the docker container above):
```bash
  ~# apt-get install sshfs
  ~# mkdir -p /mnt/nfs/tira
  ~# chown <user> /mnt/nfs/tira
  ~# chgrp <user> /mnt/nfs/tira
  ~# sshfs -o allow_other,default_permissions tira@<tira-nfs-host>:/srv/tira /mnt/nfs/tira
  ~# useradd -u 1010 tira -m -s /bin/bash
```  

