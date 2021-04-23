from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField


class DialogForm(FlaskForm):
    content = TextAreaField("Содержание")
    submit = SubmitField('Отправить')
