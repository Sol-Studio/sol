import sys
import tensorflow.keras
from PIL import Image
from PIL import ImageOps
import numpy as np
print(sys.argv)

img = sys.argv[1]
file = sys.argv[2]
index = open("ai/labels.txt").read().split("\n")
np.set_printoptions(suppress=True)
model = tensorflow.keras.models.load_model('ai/model.h5')
data = np.ndarray(shape=(1, 224, 224, 3), dtype=np.float32)
image = Image.open(img)
size = (224, 224)
image = ImageOps.fit(image, size, Image.ANTIALIAS)
image_array = np.asarray(image)
normalized_image_array = (image_array.astype(np.float32) / 127.0) - 1
data[0] = normalized_image_array
prediction             = list(model.predict(data)[0])
return_dict            = {}
for i in range(len(index)):
    return_dict[float(prediction[i])] = index[i]


open("ai/result/%s.txt" % file, 'w').write(str(return_dict))
