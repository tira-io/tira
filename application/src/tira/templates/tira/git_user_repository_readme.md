# TIRA Repository for User {{ user_name }}

This repository will contain the code and docker images for the user {{ user_name }}.
Users have full access to the docker registry of this project and can add, delete, and update images as they want.
TIRA takes care of archiving docker images used in software submissions, so users do not have to pay attention to this.

Users can use the token with the name `{{ repo_name }}` and the token `{{ token }}` to access the docker registry.

# Push Images to your docker registry

## Create an docker image

Your docker images have to use the prefix `{{ image_prefix }}`.
Create a docker image with this prefix.
For instance, the following command uses the [docker build](https://docs.docker.com/engine/reference/commandline/build/) command to create a docker image that prints "This is my software..." to standard out and assigns this image the tag `{{ image_prefix }}my-software:0.0.1`:

```
echo -e "FROM bash\nENTRYPOINT echo 'This is my software...'" |docker build -t {{ image_prefix }}my-software:0.0.1 -f - .
```

## Push the docker image

Login to your dedicated docker registry via:
```
docker login -u {{ repo_name }} -p{{ token }} registry.webis.de
```

After Login, you can upload your image via:

```
docker push {{ image_prefix }}my-software:0.0.1
```

## Use your docker image in TIRA

After you have uploaded your image to your registry, you can select your image in the add software menu of TIRA.

