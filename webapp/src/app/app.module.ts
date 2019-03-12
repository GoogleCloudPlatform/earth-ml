import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule } from '@angular/common/http';
import { NgModule } from '@angular/core';

import { MaterialComponentsModule } from './material-components/material-components.module';
import { AppComponent } from './app.component';

import { AgmCoreModule } from '@agm/core';

import { credentials } from 'src/assets/credentials';

@NgModule({
  declarations: [
    AppComponent,
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    MaterialComponentsModule,
    AgmCoreModule.forRoot({
      apiKey: credentials.mapsKey,
      libraries: ['places'],
    }),
    HttpClientModule,
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }