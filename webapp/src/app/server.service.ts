import { Injectable } from '@angular/core';

import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ServerService {
  landsatTileURL(x: number, y: number, zoom: number, year: number) {
    return `${environment.serverURL}/tile/landsat/${x}/${y}/${zoom}/${year}`
  }

  landcoverTileURL(x: number, y: number, zoom: number, year: number) {
    return `${environment.serverURL}/tile/landcover/${x}/${y}/${zoom}/${year}`
  }
}
