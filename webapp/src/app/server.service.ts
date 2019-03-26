import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ServerService {
  baseURL = environment.restURL

  constructor(private http: HttpClient) { }

  landsatTileURL(x: number, y: number, zoom: number, year: number) {
    return `${this.baseURL}/landsat/tile/${x}/${y}/${zoom}/${year}`
  }

  landcoverTileURL(x: number, y: number, zoom: number, year: number) {
    return `${this.baseURL}/landcover/tile/${x}/${y}/${zoom}/${year}`
  }
}
