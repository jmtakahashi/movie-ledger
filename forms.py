from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField, BooleanField, SelectField, DateField, RadioField

from wtforms.validators import DataRequired, Email, Length, Optional
import email_validator


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6)])
    # img_url = StringField('(Optional) Image URL')


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[
                             DataRequired(), Length(min=6)])


class UserEditForm(FlaskForm):
    """Form for editing users."""

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    new_password = PasswordField('New Password', validators=[
                                 Optional(), Length(min=6)])
    img_url = StringField('(Optional) Image URL')
    password = PasswordField('Current Password', validators=[
                             DataRequired(), Length(min=6)])


class UserDeleteForm(FlaskForm):
    """Movie search form."""

    password = PasswordField('Enter Password to Confirm', validators=[
                             DataRequired(), Length(min=6)])


class MovieAddEditForm(FlaskForm):
    """Movie add form on the movie detail page."""

    title = HiddenField("title")
    year = HiddenField("year")
    actors = HiddenField("actors")
    imdb_img = HiddenField("imdb_img")
    favorite = BooleanField("Favorite")
    platform = SelectField("Platform (optional)",
                           choices=[
                               ("", ""),
                               ("netflix", "Netflix"),
                               ("amazon prime", "Amazon Prime"),
                               ("hbo max", "HBO Max"),
                               ("hulu", "Hulu"),
                               ("apple tv", "Apple TV")
                           ]
                           )
    date_viewed = DateField("Date Viewed", validators=[Optional()])
    date_added = HiddenField("data_added")
