import re

from flask_wtf import FlaskForm
from wtforms import HiddenField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, ValidationError

from app.config import Config


def _events():
    return [(e, e) for e in Config.EVENTS]


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=128)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class CertificateForm(FlaskForm):
    event = SelectField("Event", choices=_events(), validators=[DataRequired()])
    verification_code = StringField(
        "Verification code (6 characters, leave blank to generate)",
        validators=[Optional(), Length(min=0, max=6)],
    )
    name = StringField("Full name", validators=[DataRequired(), Length(max=256)])
    institution = StringField("Institution", validators=[DataRequired(), Length(max=256)])
    segment = StringField("Segment", validators=[DataRequired(), Length(max=256)])
    prize_place = StringField(
        "Prize place", validators=[DataRequired(), Length(max=256)]
    )
    installment = StringField(
        "Installment", validators=[DataRequired(), Length(max=256)]
    )
    submit = SubmitField("Save")

    def validate_verification_code(self, field):
        raw = (field.data or "").strip()
        if not raw:
            return
        if len(raw) != 6 or not re.match(r"^[A-Za-z0-9]{6}$", raw):
            raise ValidationError("Must be exactly 6 alphanumeric characters.")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(
        "Current password", validators=[DataRequired()]
    )
    new_password = PasswordField(
        "New password",
        validators=[DataRequired(), Length(min=8, max=128)],
    )
    confirm_password = PasswordField(
        "Confirm new password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Update password")


class GenerateApiTokenForm(FlaskForm):
    generate_token = SubmitField("Generate new API token")
