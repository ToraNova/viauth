'''
withroles.py: extension of persistdb, with role-based accounts
expect database system (interact with sqlalchemy)
'''
from flask import render_template, request, redirect, abort, flash, url_for
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from viauth import source, sqlorm, persistdb, basic
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

class AuthRole(sqlorm.Base):
    __tablename__ = "authrole"
    id = Column(Integer, primary_key = True)
    name = Column(String(50),unique=True,nullable=False)
    level = Column(Integer, unique=False, nullable=False)
    auth_users = relationship('AuthUser', back_populates='parent')

    @classmethod
    def create_table(cls, dburi):
        engine = sqlorm.make_engine(dburi)
        cls.__table__.create(engine)
        engine.dispose() #house keeping

    def __init__(self, reqform):
        self.name = reqform.get('name')
        self.level = reqform.get('level')

# TODO: an architecture for role-based auth
