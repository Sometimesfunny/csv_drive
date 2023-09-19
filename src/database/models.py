from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID, primary_key=True)
    username = Column(String)
    hashed_password = Column(String)

class File(Base):
    __tablename__ = 'files'

    id = Column(UUID, primary_key=True)
    name = Column(String)
    owner_id = Column(UUID, ForeignKey('users.id'))
    column_order = Column(String)

class Data(Base):
    __tablename__ = 'data'

    id = Column(UUID, primary_key=True)
    file_id = Column(UUID, ForeignKey('files.id'))
    column_name = Column(String)
    row_number = Column(Integer)
    data = Column(String)

class FileAccess(Base):
    __tablename__ = 'file_access'

    id = Column(UUID, primary_key=True)
    file_id = Column(UUID, ForeignKey('files.id'))
    user_id = Column(UUID, ForeignKey('users.id'))
