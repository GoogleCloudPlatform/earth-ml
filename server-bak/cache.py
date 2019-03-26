import threading
from google.cloud import firestore
from google.cloud import storage


def gcs_file_exists(gcs_path):
  storage_client = storage.Client()
  bucket, path = gcs_path.lstrip('gs://').split('/', 1)
  return storage_client.bucket(bucket).blob(path).exists()


class Cache:
  def __init__(self, collection):
    self.db = firestore.Client()
    self.collection = self.db.collection(collection)
    self.lock = threading.Lock()

  # Emulate the dict interface.
  def __len__(self):
    raise NotImplementedError()

  def __getitem__(self, key):
    return self.collection.document(key).get().to_dict()

  def __setitem__(self, key, value):
    self.collection.document(key).set(value)

  def __delitem__(self, key):
    raise NotImplementedError()

  def __iter__(self):
    raise NotImplementedError()

  def __contains__(self, key):
    return self.collection.document(key).get().exists

  def __repr__(self):
    raise NotImplementedError()

  def __str__(self):
    raise NotImplementedError()

  def update(self, key_values):
    raise NotImplementedError()

  def clear(self):
    for doc in self.collection.get():
      doc.reference.delete()

  def keys(self):
    raise NotImplementedError()

  def values(self):
    raise NotImplementedError()

  def items(self):
    raise NotImplementedError()

  def get(self, key, default=None):
    raise NotImplementedError()

  def pop(self, key, default=None):
    raise NotImplementedError()

  def popitem(self):
    raise NotImplementedError()

  def dict(self):
    raise NotImplementedError()

  # Custom methods.
  def update_fields(self, key, fields):
    self.collection.document(key).update(fields)

  def set_if_unset(self, key, function):
    if key in self:
      return False
    with self.lock:
      if key not in self:
        self[key] = function()
        return True
    return False

  def get_or_set(self, key, function):
    if key in self:
      return self[key]
    with self.lock:
      if key not in self:
        self[key] = function()
    return self[key]

  def update_if_unset(self, key, field, function):
    if not self.set_if_unset(key, function):
      return True
    doc = self.collection.document(key)
    with self.lock:
      try:
        doc.get().get(field)
        return False
      except KeyError:
        doc.update(function())
        return True


blocks = Cache('blocks')
