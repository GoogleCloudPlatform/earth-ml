# Web App

This project was generated with [Angular CLI](https://github.com/angular/angular-cli) version 7.2.1.

## Credentials
You will have to specify your Google Maps API Key through a configuration file.

```typescript
// file: src/assets/credentials.ts
export const credentials = {
  mapsKey: 'Your Maps API Key',
}
```

## Development server

Run `ng serve` for a dev server. Navigate to `http://localhost:4200/`. The app will automatically reload if you change any of the source files.

Run `ng serve --prod` for a local server pointing to the production Rest API. Navigate to `http://localhost:4200/`. The app will automatically reload if you change any of the source files.

## Code scaffolding

Run `ng generate component component-name` to generate a new component. You can also use `ng generate directive|pipe|service|class|guard|interface|enum|module`.

## Build

Run `ng build` to build the project. The build artifacts will be stored in the `dist/` directory. Use the `--prod` flag for a production build.

## Running unit tests

Run `ng test` to execute the unit tests via [Karma](https://karma-runner.github.io).

## Running end-to-end tests

Run `ng e2e` to execute the end-to-end tests via [Protractor](http://www.protractortest.org/).

## Further help

To get more help on the Angular CLI use `ng help` or go check out the [Angular CLI README](https://github.com/angular/angular-cli/blob/master/README.md).


## Deploying to App Engine

```sh
ng build --prod
gcloud app deploy
```
