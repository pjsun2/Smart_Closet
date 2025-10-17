<<<<<<< HEAD
from db_ import db

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
=======
from db import db

class User(db.Model):
    __tablename__ = "users"
    id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
>>>>>>> 2576b934654217a87e1ce2c0d184f6c8243f0e19
    name = db.Column(db.String(50), nullable=False)

    def to_dict(self):
        return {"id": self.id, "name": self.name}
