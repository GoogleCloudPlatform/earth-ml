import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root'
})
export class ServerService {
  baseURL = 'http://127.0.0.1:4213'

  constructor(private http: HttpClient) { }

  landsatTileURL(x: number, y: number, zoom: number, year: number) {
    return `${this.baseURL}/landsat8/${x}/${y}/${zoom}/${year}`
  }

  landcoverTileURL(x: number, y: number, zoom: number, year: number) {
    return `${this.baseURL}/landcover/${x}/${y}/${zoom}/${year}`
  }
}
