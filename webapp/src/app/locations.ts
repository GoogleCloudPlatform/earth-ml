export class DemoLocation {
  coords: google.maps.LatLng
  bounds: google.maps.LatLngBounds
  constructor(
    public name: string, public description: string,
    latLng: [number, number], public zoom: number,
    nesw: [number, number, number, number],
  ) {
    this.coords = new google.maps.LatLng(latLng[0], latLng[1])
    this.bounds = new google.maps.LatLngBounds(
      new google.maps.LatLng(nesw[2], nesw[3]),
      new google.maps.LatLng(nesw[0], nesw[1]),
    )
  }
}

export function makeDemoLocations() {
  return [

    // Not yet visible from Landsat 8
    // - Great Green Wall in Africa
    // - Grain-for-Green Project in China
    // - Amazon Reforestation in Brazil and Peru

    new DemoLocation(
      'Boeng Peae Wildlife Sanctuary', 'Cambodia',
      [13.2066924,104.9906209], 11,
      [21.943045533438177, 106.975, 11.078401873711782, 95.625],
    ),

    new DemoLocation(
      'Madre de Dios Mine', 'Peru',
      [-12.9885315, -69.9650184], 12,
      [5.615985819155334, -50.525, -16.73619187839766, -73.125],
    ),

    new DemoLocation(
      'Rondônia', 'Brazil',
      [-9.4528783,-64.9692096], 8,
      [5.615985819155334, -50.525, -16.73619187839766, -73.125],
    ),

    new DemoLocation(
      'Beijing 北京市', 'China',
      [39.8865627,116.3692311], 9,
      [45.089035564831015, 123.85, 36.49788913307021, 112.5],
    ),

    new DemoLocation(
      'Shenzhen 深圳市', 'Guangdong, China',
      [22.6342193,113.8135933], 10,
      [31.952162238024968, 123.85, 21.843045533438175, 106.875],
    ),

    new DemoLocation(
      'Suzhou 苏州市', 'Jiangsu, China',
      [31.226347,120.2169554], 10,
      [31.952162238024968, 123.85, 21.843045533438175, 106.875],
    ),

    new DemoLocation(
      'Al Khiran الخيران', 'Kuwait',
      [28.6567696,48.2603528], 11,
      [31.952162238024968, 56.35, 21.843045533438175, 45.0],
    ),

    new DemoLocation(
      'Cananea Mine', 'Sonora, Mexico',
      [30.9795476,-110.3203144], 12,
      [52.48278022207821, -61.775, 16.536191878397652, -129.375],
    ),

    new DemoLocation(
      'Guadalajara', 'Jalisco, Mexico',
      [20.4738452,-103.2796652], 10,
      [52.48278022207821, -61.775, 16.536191878397652, -129.375],
    ),

    new DemoLocation(
      'Taupo', 'New Zealand',
      [-38.9254622,175.9834146], 9,
      [-31.952162238024968, 180.1, -49.02249926375824, 163.125],
    ),

    new DemoLocation(
      'Singapore', 'Singapore',
      [1.3492432,103.748114], 11,
      [5.615985819155334, 106.975, -0.1, 101.25],
    ),

    new DemoLocation(
      'Istanbul', 'Turkey',
      [41.1132295,29.0205794], 10,
      [45.089035564831015, 33.85, 36.49788913307021, 22.5],
    ),

    new DemoLocation(
      'Cape Cod', 'Massachusetts',
      [41.7988246, -70.5882979], 10,
      [52.48278022207821, -61.775, 16.536191878397652, -129.375],
    ),

    new DemoLocation(
      'Las Vegas', 'Nevada',
      [36.1251958, -115.1], 10,
      [52.48278022207821, -61.775, 16.536191878397652, -129.375],
    ),

    new DemoLocation(
      'Dubai دبي', 'United Arab Emirates',
      [25.1566713,55.2189301], 10,
      [31.952162238024968, 56.35, 21.843045533438175, 45.0],
    ),

  ]
}


// Cologne, Germany
// 6.435233992240934
// 50.94999148361736

// New Cairo City مدينة القاهرة الجديدة, Cairo Governorate, Egypt
// Urban growth, very fast
// 31.3470295
// 30.0177916

// Doha الدوحة, Qatar
// Farming in the desert
// 51.31268909575576
// 25.19030787757275

// Shenzhen
// 113.1325497
// 22.8628474

// Houston
// -95.44529631421166
// 29.74140736826767

// Brisbane, Queensland, Australia
// Coast reshaping
// 153.19638244061258
// -27.412562979777352

// Cananea Mine, Sonora, Mexico
// Mining
// -110.37536271621093
// 30.97172792497669

// Singapore
// 103.564045
// 1.3139843

// Rwanda
// 28.7589167
// -1.9432847

// Swiss Alps
// 7.6055472
// 46.4016925

// Mexico City
// -99.15498598857971
// 19.410761813668095

// Seattle
// -122.34658356313494
// 47.71131339800126

// Vancouver
// -122.50195172968668
// 49.10252831912233

// Oslo
// 10.577184567656625
// 59.927105532599036

// Pompeii
// 14.44492103112291
// 40.785579197365585

// Istanbul
// 28.99432926475204
// 41.09019648474241

// Prypyat
// 30.063155477083793
// 51.37953821370403

// Jakarta
// 106.80738893418841
// -6.129147133417564

// Lena River
// 124.9444087420382
// 64.79987391232582




// ------


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
