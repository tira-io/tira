This folder contains files that are **only** relevant for setting up a mock environment for development. The subfolder
`authelia` contains an customized
[configuration file](https://github.com/authelia/authelia/blob/v4.38.8/config.template.yml) for
[Authelia](https://www.authelia.com/) and a user database containing some mock users and admins. The configuration files
for the reverse proxy (inside `nginx`) are copied with only slight modifications from Authelia's
[Guide](https://www.authelia.com/integration/proxies/nginx/) and the certificates are self-signed since we need https
for the auth provider (Authelia) to be happy.

If the certificates expired, you can run
```sh
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout tira-dev-selfsigned.key -out tira-dev-selfsigned.crt
```
to generate new ones.