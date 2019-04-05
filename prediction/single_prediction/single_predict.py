import os
import time
import datetime
import sys
import tensorflow as tf
slim = tf.contrib.slim

SPATIAL_FEATURES_KEY = 'spatial_features'
FEATURES_KEY = 'features'
LABELS_KEY = 'labels'

LANDCOVER_CLASSES_N = 10

PREDICT_OUTPUT_L = 256
PREDICT_PADDING = 16


config = {'encoder_extra_convolutions': 1,
          'encoder_channel_init': 29,
          'encoder_channel_mul': 1.8030832537902222,
          'encoder_core_n': 1,
          'extra_block': True,
          'classes': LANDCOVER_CLASSES_N}


def chunks(items, count):
    li = len(items)
    smallest_size = li // count
    n_biggers = li % count
    lengths = [smallest_size] * count
    for i in range(n_biggers):
        lengths[i] += 1
    partitions = []
    starting = 0
    for l in lengths:
        partitions.append(items[starting: starting + l])
        starting += l
    return partitions


def blindspotv2_encoder(inputs, channel_in_n, channel_out_n, config):
    rdx = inputs

    for _ in range(0, 1 + config['encoder_extra_convolutions']):
        rdx = slim.separable_conv2d(rdx, num_outputs=channel_in_n)

    residual = slim.conv2d(inputs, num_outputs=channel_in_n, kernel_size=[1, 1])

    pre_downscale = tf.concat([rdx, residual], axis=3)
    return slim.separable_conv2d(pre_downscale,
                                 num_outputs=channel_out_n,
                                 stride=2)


def blindspotv2_decoder(inputs, residual, residual_pre_n, channel_out_n, conf):
    newSize = [tf.shape(residual)[1], tf.shape(residual)[2]]
    block_scaled = tf.image.resize_images(inputs, newSize)
    block_scaled = slim.conv2d(
        block_scaled,
        kernel_size=[1, 1],
        num_outputs=channel_out_n)

    proc_res = slim.conv2d(
        residual,
        kernel_size=[1, 1],
        num_outputs=residual_pre_n)
    block_scaled = tf.concat([block_scaled, proc_res], axis=3)
    block_scaled = slim.separable_conv2d(
        block_scaled,
        num_outputs=channel_out_n)
    return block_scaled


def get_channels(stage, config):
    return int(config['encoder_channel_init'] *
               pow(config['encoder_channel_mul'], stage))


def blindspotv2(spatial_inputs, instance_inputs, training, config):
    with slim.arg_scope([slim.conv2d, slim.separable_conv2d],
                        kernel_size=[3, 3],
                        normalizer_fn=slim.batch_norm,
                        normalizer_params={'is_training': training}):
        with slim.arg_scope([slim.separable_conv2d], depth_multiplier=1):
            input0 = slim.conv2d(spatial_inputs, kernel_size=[1, 1],
                                 num_outputs=get_channels(0, config))
            input1 = slim.conv2d(input0, num_outputs=get_channels(0, config),
                                 stride=2)

            block = input1
            block_first = blindspotv2_encoder(block,
                                              get_channels(1, config),
                                              get_channels(2, config),
                                              config)
            block = block_first

            block_last = blindspotv2_encoder(block,
                                             get_channels(2, config),
                                             get_channels(3, config),
                                             config)

            block = block_last
            if config['extra_block']:
                block = blindspotv2_encoder(block,
                                            get_channels(3, config),
                                            get_channels(4, config),
                                            config)

            core_channel_count = 3 + (1 if config['extra_block'] else 0)

            blockRows = tf.shape(block)[1]
            blockCols = tf.shape(block)[2]
            expanded_features = tf.expand_dims(instance_inputs, axis=1)
            expanded_features = tf.expand_dims(expanded_features, axis=2)
            expanded_features = tf.tile(expanded_features,
                                        [1, blockRows, blockCols, 1])

            block = tf.concat([expanded_features, block], axis=3)
            block_res = slim.conv2d(
                block,
                kernel_size=[1, 1],
                num_outputs=get_channels(core_channel_count, config))

            for i in range(0, config['encoder_core_n']):
                block = slim.separable_conv2d(
                    block,
                    num_outputs=get_channels(core_channel_count, config))

            block = tf.concat([block_res, block], axis=3)
            block = slim.conv2d(
                block,
                get_channels(core_channel_count, config),
                kernel_size=[1, 1])

            block_scaled = blindspotv2_decoder(block,
                                               block_first,
                                               get_channels(1, config),
                                               get_channels(
                                                   core_channel_count - 1,
                                                   config),
                                               config)

            block_scaled = blindspotv2_decoder(block_scaled,
                                               input0,
                                               get_channels(0, config),
                                               get_channels(
                                                   core_channel_count - 2,
                                                   config),
                                               config)

            block_scaled = slim.separable_conv2d(
                block_scaled,
                num_outputs=get_channels(core_channel_count - 2, config))

            return slim.conv2d(block_scaled, config['classes'],
                               kernel_size=[1, 1],
                               activation_fn=None)


def create_model_fn(config):
    def model_fn(features, labels, mode):
        spatial = features['spatial']
        inp_features = features['fixed']
        mask = features['mask']

        output = blindspotv2(
            spatial, inp_features, mode == tf.estimator.ModeKeys.TRAIN, config)

        if mode == tf.estimator.ModeKeys.PREDICT:
            land_cover = tf.argmax(output, axis=3)
            land_cover = tf.slice(
                land_cover,
                [0, PREDICT_PADDING, PREDICT_PADDING],
                [-1, PREDICT_OUTPUT_L, PREDICT_OUTPUT_L])
            return tf.estimator.EstimatorSpec(
                mode=mode, predictions={'predictions': land_cover})
        return None

    return model_fn


def predict_fn(file_names):
    ds = tf.data.TFRecordDataset(file_names, 'GZIP')

    side_l = PREDICT_OUTPUT_L + 2 * PREDICT_PADDING

    def parse(example_proto):
        feature_columns = {
            'B1': tf.FixedLenFeature([side_l, side_l], dtype=tf.float32),
            'B2': tf.FixedLenFeature([side_l, side_l], dtype=tf.float32),
            'B3': tf.FixedLenFeature([side_l, side_l], dtype=tf.float32),
            'B4': tf.FixedLenFeature([side_l, side_l], dtype=tf.float32),
            'B5': tf.FixedLenFeature([side_l, side_l], dtype=tf.float32),
            'B6': tf.FixedLenFeature([side_l, side_l], dtype=tf.float32),
            'B7': tf.FixedLenFeature([side_l, side_l], dtype=tf.float32),
            'B10': tf.FixedLenFeature([side_l, side_l], dtype=tf.float32),
            'B11': tf.FixedLenFeature([side_l, side_l], dtype=tf.float32),
            'latitude': tf.FixedLenFeature([side_l, side_l],
                                           dtype=tf.float32),
            'elevation': tf.FixedLenFeature([side_l, side_l],
                                            dtype=tf.float32),
        }
        parsed_features = tf.parse_single_example(example_proto,
                                                  feature_columns)
        centered = tf.stack([
            parsed_features['B1'],
            parsed_features['B2'],
            parsed_features['B3'],
            parsed_features['B4'],
            parsed_features['B5'],
            parsed_features['B6'],
            parsed_features['B7'],
            parsed_features['B10'],
            parsed_features['B11'],
            parsed_features['latitude'],
            parsed_features['elevation'],
        ],
            axis=0)
        spatial_features = tf.transpose(centered, [1, 2, 0])
        test_features = tf.stack([
            tf.constant(-0.8403242422804175),
            tf.constant(-0.5420840966453842)],
            axis=0)
        test_features = tf.reshape(test_features, [2])
        fixed_features = test_features

        return spatial_features, fixed_features

    ds = ds.map(parse, num_parallel_calls=5)
    ds = ds.batch(1)

    iterator = ds.make_one_shot_iterator()
    (spatial, fixed) = iterator.get_next()
    return {'spatial': spatial, 'fixed': fixed,
            'mask': tf.ones([side_l, side_l, 1])}


def make_example(pred_dict):
    return tf.train.Example(
        features=tf.train.Features(
            feature={
                'p': tf.train.Feature(
                    int64_list=tf.train.Int64List(
                        value=pred_dict['predictions'].flatten()))
            }
        )
    )


def predict(input_files, model_dir, output_file):
    now = datetime.datetime.now()
    print('Starting at: {}'.format(now.strftime("%Y-%m-%d %H:%M")))
    model = tf.estimator.Estimator(model_fn=create_model_fn(config),
                                   model_dir=model_dir)

    predictions = model.predict(
        input_fn=lambda: predict_fn(file_names=input_files))

    MAX_RECORDS_PER_FILE = 100000

    still_writing = True
    total_patches = 0
    while still_writing:
        sys.stdout.flush()
        writer = tf.python_io.TFRecordWriter(output_file)
        print('Writing file: {}'.format(output_file))
        try:
            written_records = 0
            while True:
                pred_dict = predictions.__next__()

                writer.write(make_example(pred_dict).SerializeToString())

                written_records += 1
                total_patches += 1

                if written_records % 5 == 0:
                    print('  Writing patch: {}'.format(written_records))

                if written_records == MAX_RECORDS_PER_FILE:
                    break
        except Exception as e:
            print(str(e))
            still_writing = False
        finally:
            writer.close()

    print('Wrote: {} patches.'.format(total_patches))


if __name__ == '__main__':
    start_time = time.time()
    model_dir = os.environ['MODELDIR']
    in_file = os.environ['INPUT']
    out_file = os.environ['OUTPUT']

    print('in_file: {}'.format(in_file))
    print('out_file: {}'.format(out_file))
    print('model_dir: {}'.format(model_dir))

    tf.logging.set_verbosity(tf.logging.DEBUG)

    predict([in_file, ], model_dir, out_file)

    print('Time to finish predictions: {}'.format((time.time() - start_time)))


