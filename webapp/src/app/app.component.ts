/// <reference types="@types/googlemaps" />

import { Component, ViewChild } from '@angular/core';

import { Location, makeDemoLocations } from './locations'
import { ServerService } from './server.service';

const tileSize = 256

class Overlay {
  constructor(
    public landsat: google.maps.ImageMapType,
    public landcover: google.maps.ImageMapType,
  ) { }
}

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  title = 'Project Earth';
  state = {
    lat: 37.8195428011924,
    lng: -122.49165319668896,
    zoom: 13,
  }

  // @ts-ignore: initialized by Angular.
  @ViewChild('searchBox') searchBox: ElementRef

  // Locations
  locations: Location[] = []

  // Yearly animation
  readonly startYear = 2014
  readonly endYear = 2018
  year = this.startYear
  overlays = new Map<number, Overlay>()  // {year: Overlay}
  yearChangeInterval = 1200  // milliseconds
  animationTimer: NodeJS.Timer | null = null

  // Landcover layer
  landcoverOpacity = 0.8

  // @ts-ignore: uninitialized value, gets initialized at onMapReady.
  setLocation: (location: Location) => void

  // @ts-ignore: uninitialized value, gets initialized at onMapReady.
  updateOverlays: () => void

  // @ts-ignore: uninitialized value, gets initialized at onMapReady.
  toggleAnimation: (start: boolean) => void

  constructor(
    private readonly server: ServerService,
  ) { }

  onMapReady($map: google.maps.Map) {
    // Initialize functions with closures to include a reference to $map.
    this.initMapMethods($map)

    // Set the map markers for all the locations.
    this.locations = makeDemoLocations()
    for (let location of this.locations) {
      location.marker.setMap($map)
      location.marker.addListener('click', () => {
        this.setLocation(location)
      })
    }
    this.setLocation(this.locations[0])

    // Set up the search box.
    let searchBox = new google.maps.places.Autocomplete(this.searchBox.nativeElement)
    searchBox.addListener('place_changed', () => {
      let place = searchBox.getPlace()
      if (!place.geometry)
        return

      if (place.geometry.viewport) {
        $map.fitBounds(place.geometry.viewport)
      } else {
        $map.setCenter(place.geometry.location)
        $map.setZoom(12)
      }
    })
    searchBox.bindTo('bounds', $map)

    // Initialize the landsat and landcover overlays for every year.
    for (let year = this.startYear; year <= this.endYear; year++) {
      let overlays = {
        landsat: new google.maps.ImageMapType({
          getTileUrl: (tile, zoom) => {
            return this.server.landsatTileURL(tile.x, tile.y, zoom, year)
          },
          tileSize: new google.maps.Size(tileSize, tileSize),
        }),
        landcover: new google.maps.ImageMapType({
          getTileUrl: (tile, zoom) => {
            return this.server.landcoverTileURL(tile.x, tile.y, zoom, year)
          },
          tileSize: new google.maps.Size(tileSize, tileSize),
        }),
      }
      this.overlays.set(year, overlays)
      $map.overlayMapTypes.push(overlays.landsat)
      $map.overlayMapTypes.push(overlays.landcover)
    }
    this.updateOverlays()

    // Set a function to run at specified intervals to update the year and the overlays.
    this.toggleAnimation(true)
  }

  initMapMethods(map: google.maps.Map) {
    this.setLocation = (location: Location) => {
      map.panTo({lat: location.lat, lng: location.lng})
      map.setZoom(location.zoom)

      // this.selectedLocation = location
      for (let loc of this.locations)
        loc.closeInfoWindow()
      location.openInfoWindow(map)
    }

    this.updateOverlays = () => {
      // `this.year` is updated from the [(value)]="year" binding in <mat-slider>.
      for (let [year, overlay] of this.overlays) {
        let visible = year == this.year ? 1 : 0
        overlay.landsat.setOpacity(visible)
        overlay.landcover.setOpacity(visible * this.landcoverOpacity)
      }
    }

    this.toggleAnimation = (start: boolean) => {
      if (start) {
        this.animationTimer = setInterval(() => {
          this.year++
          if (this.year > this.endYear)
            this.year = this.startYear
          this.updateOverlays()
        }, this.yearChangeInterval)
      } else if (this.animationTimer) {
        clearInterval(this.animationTimer)
      }
    }
  }
}
