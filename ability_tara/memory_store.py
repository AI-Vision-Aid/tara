"""Explicit standalone-local storage; never selected by the production site."""
from copy import deepcopy
from threading import RLock

class Snapshot:
    def __init__(self,data):self.data=deepcopy(data)
    def to_dict(self):return deepcopy(self.data)

class Document:
    def __init__(self,store,key):self.store,self.key=store,key
    def get(self):
        with self.store.lock:return Snapshot(self.store.data.get(self.key))
    def set(self,value,merge=False):
        with self.store.lock:
            old=self.store.data.get(self.key,{}) if merge else {}
            self.store.data[self.key]=deepcopy(old|value)
    def update(self,value):self.set(value,merge=True)

class Collection:
    def __init__(self,store,name):self.store,self.name=store,name
    def document(self,key):return Document(self.store,self.name+'/'+key)

class Store:
    def __init__(self):self.lock=RLock();self.data={}
    def collection(self,name):return Collection(self,name)

store=Store()
