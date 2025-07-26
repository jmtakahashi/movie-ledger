"""Forms for our Flask app"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, HiddenField, BooleanField, SelectField, DateField

from wtforms.validators import InputRequired, Email, Length, Optional


class UserAddForm(FlaskForm):
    """Form for adding users."""

    username = StringField('Username', validators=[
                           InputRequired(), Length(min=3)])
    email = StringField('E-mail', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[
                             InputRequired(), Length(min=6)])
    img_url = StringField('(Optional) Image URL')


class LoginForm(FlaskForm):
    """Login form."""

    email = StringField('Email', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])


class UserEditForm(FlaskForm):
    """Form for editing users."""

    username = StringField('Username', validators=[InputRequired()])
    email = StringField('E-mail', validators=[InputRequired(), Email()])
    new_password = PasswordField('New Password', validators=[
                                 Optional(), Length(min=6)])
    img_url = StringField('(Optional) Image URL')
    password = PasswordField('Current Password', validators=[
                             InputRequired()])


class UserDeleteForm(FlaskForm):
    """Movie search form."""

    password = PasswordField('Enter Password to Confirm', validators=[
                             InputRequired()])


class MovieAddEditForm(FlaskForm):
    """Movie add form on the movie detail page."""

    imdb_id = HiddenField("imdb_id", validators=[InputRequired()])
    title = HiddenField("title", validators=[InputRequired()])
    release_year = HiddenField("year", validators=[InputRequired()])
    imdb_img = HiddenField("imdb_img", validators=[InputRequired()])
    favorite = BooleanField(
        "Add/Remove to your favorites")
    platform = SelectField("Platform (optional)",
                           choices=[
                               ("", ""),
                               ("Netflix", "Netflix"),
                               ("Amazon Prime", "Amazon Prime"),
                               ("HBO Max", "HBO Max"),
                               ("Hulu", "Hulu"),
                               ("Apple TV", "Apple TV")
                           ]
                           )
    date_viewed = DateField("Date Viewed (optional)", validators=[Optional()])
    date_added = HiddenField("date_added")
