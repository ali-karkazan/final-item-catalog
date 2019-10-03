from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    items = relationship('Item', cascade="all, delete-orphan")
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # We added this serialize function to be able to
    # send JSON objects in a serializable format
    @property
    def serialize(self):

        return {
           'name': self.name,
           'id': self.id,
           'user_id': self.id
           }


class Item(Base):

    __tablename__ = 'item'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    description = Column(String(250))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    # We added this serialize function to be able to
    # send JSON objects in a serializable format
    @property
    def serialize(self):

        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'category_id': self.category_id,
            'user_id': self.user_id
        }


engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)
