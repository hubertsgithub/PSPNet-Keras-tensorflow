import os
import random
import numpy as np
from scipy.misc import imresize, imread
from scipy.ndimage import zoom
from collections import defaultdict

DATA_MEAN = np.array([[[123.68, 116.779, 103.939]]])

# To downscale image labels:
# 1) imresize with interpolation='nearest'
# 2) zoom with order=0
# 3) cv2 resize
# 4) other
# Unsure which one is the best. Just use imresize for now.

def preprocess_img(img, input_shape):
    img = imresize(img, input_shape)
    img = img - DATA_MEAN
    img = img[:, :, ::-1] # Why is this even necessary?
    img.astype('float32')
    return img

def update_inputs(batch_size = None, input_size = None, num_classes = None):
  return np.zeros([batch_size, input_size[0], input_size[1], 3]), \
    np.zeros([batch_size, input_size[0], input_size[1], num_classes])

def data_generator_s31(datadir='', nb_classes = None, batch_size = None, input_size=None, separator='_', test_nmb=50):
  if not os.path.exists(datadir):
    print("ERROR!The folder is not exist")
  #listdir = os.listdir(datadir)
  data = defaultdict(dict)
  image_dir = os.path.join(datadir, "imgs")
  image_paths = os.listdir(image_dir)
  for image_path in image_paths:
    nmb = image_path.split(separator)[0]
    data[nmb]['image'] = image_path
  anno_dir = os.path.join(datadir, "maps_bordered")
  anno_paths = os.listdir(anno_dir)
  for anno_path in anno_paths:
    nmb = anno_path.split(separator)[0]
    data[nmb]['anno'] = anno_path
  values = data.values()
  random.shuffle(values)
  return generate(values[test_nmb:], nb_classes, batch_size, input_size, image_dir, anno_dir), \
      generate(values[:test_nmb], nb_classes, batch_size, input_size, image_dir, anno_dir)

def generate(values, nb_classes, batch_size, input_size, image_dir, anno_dir):
  while 1:
    random.shuffle(values)
    images, labels = update_inputs(batch_size=batch_size,
       input_size=input_size, num_classes=nb_classes)
    for i, d in enumerate(values):
      img = imresize(imread(os.path.join(image_dir, d['image']), mode='RGB'), input_size)
      y = imread(os.path.join(anno_dir, d['anno']), mode='L')
      h, w = input_size
      y = zoom(y, (1.*h/y.shape[0], 1.*w/y.shape[1]), order=1, prefilter=False)
      y = (np.arange(nb_classes) == y[:,:,None]).astype('float32')
      assert y.shape[2] == nb_classes
      images[i % batch_size] = img
      labels[i % batch_size] = y
      if (i + 1) % batch_size == 0:
        yield images, labels
        images, labels = update_inputs(batch_size=batch_size,
          input_size=input_size, num_classes=nb_classes)


def generate_ade20k(values, nb_classes, batch_size, input_size, image_dir, anno_dir):
    while 1:
        random.shuffle(values)
        images, labels = update_inputs(batch_size=batch_size,
        input_size=input_size, num_classes=nb_classes)

        for i, d in enumerate(values):

            # Input Image (H,W,3)
            img = imresize(imread(os.path.join(image_dir, d['image']), mode='RGB'), input_size)
            assert img.shape == (input_size, input_size, 3), img.shape

            # Input labels (H,W,1)
            y = imread(os.path.join(anno_dir, d['anno']), mode='L')
            y_labelset_orig = set(y.flatten())
            y = imresize(y, (input_size, input_size), interp='nearest')
            y_labelset_resized = set(y.flatten())
            assert y.shape == (input_size, input_size, 1), y.shape
            assert y_labelset_orig == y_labelset_resized

            # This is not true. If we want to use categorical cross entropy, I think channels should be 1.
            assert y.shape == (input_size, input_size, nb_classes)

            images[i % batch_size] = img
            labels[i % batch_size] = y
            if (i + 1) % batch_size == 0:
                yield images, labels
                images, labels = update_inputs(batch_size=batch_size,
                input_size=input_size, num_classes=nb_classes)


