import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class Dialogs(SqlAlchemyBase):
    __tablename__ = 'dialogs'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    users_id = sqlalchemy.Column(sqlalchemy.String)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    user = orm.relation('User')
    text = sqlalchemy.Column(sqlalchemy.String)
