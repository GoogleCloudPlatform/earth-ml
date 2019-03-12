export class Location {
  marker: google.maps.Marker
  infoWindow: google.maps.InfoWindow

  constructor(
    public name: string,
    public icon: string,
    public lat: number,
    public lng: number,
    public zoom: number,
    public description: string,
  ) {
    this.marker = new google.maps.Marker({
      title: this.name,
      position: {lat: this.lat, lng: this.lng},
    })
    this.infoWindow = new google.maps.InfoWindow({
      content: `
        <div style="color: darkslategray">
          <h2> ${this.name} </h2>
          <p> ${this.description} </p>
        </div>`,
      disableAutoPan: true,
    })
  }

  openInfoWindow(map: google.maps.Map) {
    this.infoWindow.open(map, this.marker)
  }

  closeInfoWindow() {
    this.infoWindow.close()
  }
}

export function makeDemoLocations() {
  return [
    new Location(
      'Food Forest',
      'nature_people',
      37.916690059761484,
      -122.5968212332451,
      11,
      `\
Food Forest description.`,
    ),

    new Location(
      'Golden Gate',
      'domain',
      37.816690059761484,
      -122.4968212332451,
      11,
      `\
Golden Gate Bridge description.`,
    ),

    new Location(
      'Urban Growth',
      'location_city',
      37.716690059761484,
      -122.3968212332451,
      11,
      `\
Las Vegas description.`,
    ),

  ]
}
