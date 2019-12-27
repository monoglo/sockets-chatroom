import datetime

from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    uid = Column(Integer, primary_key=True)
    nickname = Column(String(32))
    password = Column(String(32))
    last_offline_time = Column(DateTime)

    def __repr__(self):
        return "<User(uid='%s', nickname='%s', password='%s', last_offline_time='%s')>" % (
            self.uid, self.nickname, self.password, self.last_offline_time)


class UserLogin(Base):
    __tablename__ = 'user_login'
    uid = Column(Integer, primary_key=True)
    ip_address = Column(String)
    login_time = Column(DateTime)

    def __repr__(self):
        return "<UserLogin(uid='%s', ip_address='%s', login_time='%s')>" % (
            self.uid, self.ip_address, self.login_time)


class Message(Base):
    __tablename__ = 'messages'
    mid = Column(Integer, primary_key=True)
    sender_uid = Column(Integer)
    sender_ip = Column(String)
    receiver_uid = Column(String)
    message = Column(String)
    group_gid = Column(Integer)
    create_time = Column(DateTime)

    def __repr__(self):
        return "<Message(mid='%s', sender_uid='%s', sender_ip='%s',receiver_uid='%s', message='%s', group_gid='%s', " \
               "create_time='%s')>" % (
                   self.mid, self.sender_uid, self.sender_ip, self.sender_uid, self.message, self.group_gid,
                   self.create_time)


class Group(Base):
    __tablename__ = 'groups'
    gid = Column(Integer, primary_key=True)
    group_name = Column(String)
    create_time = Column(DateTime)

    def __repr__(self):
        return "<Group(gid='%s', group_name='%s', create_time='%s')>" % (
            self.gid, self.group_name, self.create_time)


class GroupUsers(Base):
    __tablename__ = 'group_users'
    rid = Column(Integer, primary_key=True)
    gid = Column(Integer)
    uid = Column(Integer)
    join_time = Column(DateTime)

    def __repr__(self):
        return "<GroupUsers(rid='%s', gid='%s', uid='%s', join_time='%s')>" % (
            self.rid, self.gid, self.uid, self.join_time)

'''
t = datetime.datetime.now()
engine = create_engine('sqlite:///db/ChatServer.db')
user = User(uid='1', nickname='yingrui', password='123456', last_offline_time=t)
DBSession = sessionmaker(bind=engine)
session = DBSession()
session.add(user)
session.commit()
session.close()
'''
