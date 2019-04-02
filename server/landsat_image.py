import ee
import math

def get(year):
  # Create the Landsat 8 Surface Reflectance image.
  image = (
      ee.ImageCollection('LANDSAT/LC08/C01/T1_SR')
      .filterDate(f"{year}-1-1", f"{year}-12-31")
      .map(mask_clouds)
      .median()
  )

  # Normalize the band values to a range from 0 to 1.
  optical_bands = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']
  max_optical_value = 10000

  thermal_bands = ['B10', 'B11']
  min_thermal_value = 273.15  # Kelvin, freezing point
  max_thermal_value = 373.15  # Kelvin, boiling point

  image = (
      image.select(optical_bands).divide(max_optical_value)
      .addBands(
          image.select(thermal_bands).multiply(0.1)
          .clamp(min_thermal_value, max_thermal_value)
          .subtract(min_thermal_value).multiply(0.01)
      )
  )

  # Add normalized elevation.
  max_elevation = 4373
  elevation = (
    ee.Image('JAXA/ALOS/AW3D30_V1_1')
    .select('AVE').divide(max_elevation).rename('elevation')
  )
  image = image.addBands(elevation)

  # Add normalized latitude band.
  max_angle = 90
  latitude = ee.Image.pixelLonLat().select(['latitude']).divide(max_angle)
  image = image.addBands(latitude)

  # Add normalized time projection bands.
  time_angle = ee.Date(f"{year}-1-1").getFraction('year').multiply(2 * math.pi)
  time_projected_x = ee.Image(time_angle.sin()).rename('time_x')
  time_projected_y = ee.Image(time_angle.cos()).rename('time_y')
  image = image.addBands(time_projected_x).addBands(time_projected_y)

  return image.double()


def mask_clouds(image):
  qa = image.select('pixel_qa')

  cloud_shadow_bit = ee.Number(2**3).int()
  cloud_shadow_mask = qa.bitwiseAnd(cloud_shadow_bit).eq(0)

  clouds_bit = ee.Number(2**5).int()
  clouds_mask = qa.bitwiseAnd(clouds_bit).eq(0)

  return image.updateMask(cloud_shadow_mask.And(clouds_mask))
