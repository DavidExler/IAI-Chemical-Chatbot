# Frontend

The Frontend is written in Angular.
Per default it will force a login via Keycloak when the chatbot is accessed or reloaded, to better protect sensitive data provided by the chatbot.
Change this in the app.module.ts if needed.


## Development

### Development server

Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The application will automatically reload if you change any of the source files.

### Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

### Build

Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory (not included here).
If you want to use a locally built frontend, parse it to the chatbot/frontend/dist directory

### Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

### Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via a platform of your choice. To use this command, you need to first add a package that implements end-to-end testing capabilities.

### Further help

To get more help on the Angular CLI use `ng help` or go check out the [Angular CLI Overview and Command Reference](https://angular.dev/tools/cli) page.

## Docker Container

### frontend

- **Image**: self-hosted (ghrc) or self-built.
- **Description**: Hosting our Frontend inside a Nginx container.
- **Url**: [http://iai-ml4home028.iai.kit.edu/chat](http://iai-ml4home028.iai.kit.edu/chat)
- **Known Issues** This repository does not assume https support in the network it is deployed in.
    - HTTP access can be marked as 'not secure' by some browsers.
    - Some browsers cache unsuccessful connection attempts with HTTPS instead of HTTP automatically. Use a private tab or clear the cache in this case.
- **Additional Info** If your build is not a deployed production build, this Service can be used for everything for simplicity. For your final version, the access to the local Volumes this Service is given should be commented out or deleted.


### frontend-staging

- **Image**: self-built
- **Description**: Hosting our Frontend inside a Nginx container. This is the staging environment.
- **Url**: [http://iai-ml4home028.iai.kit.edu/chat-staging](http://iai-ml4home028.iai.kit.edu/chat-staging)
- **Additional Info** This Service is only necessary if you are testing changes that must not be published to a running production build 