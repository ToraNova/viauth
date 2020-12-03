#--------------------------------------------------
# fsqlite.py (sqlalchemy ORM base)
# this file is static and should not be tampered with
# it initializes the required base models for the db engine
# introduced 8/12/2018
# migrated from rapidflask to miniflask (22 Jul 2020)
# migrated from miniflask to vials project (29 Nov 2020)
# ToraNova 2020
# chia_jason96@live.com
#--------------------------------------------------

from collections import namedtuple
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

DBstruct = namedtuple("DBstruct", ["engine","metadata","session","base"])
Base = declarative_base()

def make_dbstruct(dburi):
    '''deprecated, but kept for references'''
    engine = create_engine(dburi,convert_unicode=True)
    metadata = MetaData(bind=engine)
    session = make_session(engine)
    base = declarative_base()
    base.query = session.query_property()
    return DBstruct(engine, metadata, session, base)

def make_session(engine):
    '''create a session and bind the Base query property to it'''
    sess =  scoped_session(sessionmaker(autocommit=False,autoflush=False,bind=engine))
    global Base
    Base.query = sess.query_property()
    return sess

def make_engine(dburi, convert_unicode=True):
    '''create an engine based on an uri
    if the engine does not persist and a new one will be created sooner, call the
    Engine.dispose() method'''
    return create_engine(dburi, convert_unicode=convert_unicode)

def connect(dburi):
    '''easy function to connect to a database, returns a session'''
    engine = make_engine(dburi)
    return make_session(engine)
