# Webserver

We are using a Nginx Reverse Proxy to serve the Chatbot.
This allows us to use a single domain for multiple services.
The Nginx Reverse Proxy is configured to route requests to the correct service based on the path.

You can read more about the Nginx Reverse Proxy in the [official documentation](https://github.com/nginx-proxy/nginx-proxy).

## Add Container to Webserver Network

Add the following to the `docker-compose.yml` of the service you want to add to the webserver network.

```yaml
services:
  service_name:
    ...
    environment:
      VIRTUAL_HOST: iai-ml4home028.iai.kit.edu # Domain
      VIRTUAL_PORT: 80                         # Port (inside the container)
      VIRTUAL_PATH: /chat/                     # Subpath
    networks:
      - webserver
    ...
networks:
  # Use external webserver network
  webserver:
    external: true
```
