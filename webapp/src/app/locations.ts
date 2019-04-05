export class Location {
  marker: google.maps.Marker
  infoWindow: google.maps.InfoWindow

  constructor(
    public name: string,
    public description: string,
    public icon: string,
    public lng: number,
    public lat: number,
    public zoom: number,
  ) {
    this.marker = new google.maps.Marker({
      title: this.name,
      position: {lng: this.lng, lat: this.lat},
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

// landscape
// nature
// nature_people
// wb_cloudy
// wb_sunny
// ac_unit
// domain
// location_city
// public
// whatshot
// star

export function makeDemoLocations() {
  return [

    new Location(
      'Suzhou 苏州市',
      'Jiangsu, China',
      'landscape',
      120.3641085,
      31.3286305,
      10,
    ),

    new Location(
      'Rondônia',
      'Brazil',
      'landscape',
      -65.5369773,
      -10.8179813,
      8,
    ),

    new Location(
      'Cape Cod',
      'Massachusetts, USA',
      'landscape',
      -70.5882979,
      41.7988246,
      10,
    ),

    new Location(
      'Dubai دبي',
      'United Arab Emirates',
      'landscape',
      54.9475504,
      25.0757073,
      10,
    ),

  ]
}

// Boeng Peae Wildlife Sanctuary ដែនជំរកសត្វព្រៃបឹងពេរ, Cambodia
// Deforestation for cropland
// 13.1988931,104.5836819,10.01z
// 13.209963,104.2266191,8.26z


// Al Khiran الخيران, Kuwait
// Man-made channels
// 48.36183131164036
// 28.659249074418803

// Aral Sea, Orol Dengizi, Kazakhstan
// Decreasing water level
// 59.404562793604235
// 45.200090904146826

// Keller, Texas, United States (?)
// Urban growth
// -97.28903854596484
// 32.929769555965095

// Beijing 北京市, China
// Urban growth, fast
// 116.37269927441412
// 39.922748854953895

// Brisbane, Queensland, Australia
// Coast reshaping
// 153.19638244061258
// -27.412562979777352

// Busan 부산광역시, South Korea
// Urban growth
// 128.94304317363276
// 35.150826985330916

// New Cairo City مدينة القاهرة الجديدة, Cairo Governorate, Egypt
// Urban growth, very fast
// 31.3470295
// 30.0177916

// Cananea Mine, Sonora, Mexico
// Mining
// -110.37536271621093
// 30.97172792497669

// Chongqing 重庆市, China
// Urban growth
// 106.56895140628589
// 29.514408488378315

// Cologne Köln, Germany
// Terraforming
// 6.313014213291215
// 50.94088068353434

// Columbia Glacier, Alaska (?)
// Decreasing ice levels
// -149.99915419801934
// 59.970415439023036

// Dead Sea
// Decreasing water levels
// 35.46757539121945
// 31.330154894320078

// Doha الدوحة, Qatar
// Farming in the desert
// 51.31268909575576
// 25.19030787757275

// Drebkau, Germany
// Terraforming
// 14.240889368953527
// 51.66589691482953
