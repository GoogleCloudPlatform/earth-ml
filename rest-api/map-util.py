import argparse
import datetime
import os
import subprocess as sp

import cache
import config
import landcover
import uploader


def delete_all():
  cache.regions.clear()
  asset_id = '/'.join([config.ee_project, config.ee_image_collection])
  sp.run(uploader.earthengine + ['rm', '-v', '-r', asset_id])
  sp.run(uploader.earthengine + ['create', 'collection', asset_id])


def process_all():
  for year in range(2014, datetime.datetime.now().year):
    landcover.request_tile_regions(0, 0, 0, year)


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter,
  )
  parser.add_argument(
      '--delete-all',
      action='store_true',
      default=False,
      help='Deletes all the images from the image collection.',
  )
  parser.add_argument(
      '--process-all',
      action='store_true',
      default=False,
      help='Processes landcover for all the world from year 2014 to present',
  )
  args = parser.parse_args()

  done_something = False

  if args.delete_all:
    delete_all()
    done_something = True

  if args.process_all:
    process_all()
    done_something = True

  if not done_something:
    print('Note: no action taken.')
    parser.print_help()
