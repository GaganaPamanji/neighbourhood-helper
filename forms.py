from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, BooleanField
from wtforms import IntegerField, DateTimeField, SubmitField, RadioField, ValidationError
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    user_type = RadioField('I am a:', choices=[('volunteer', 'Volunteer'), 
                                              ('recipient', 'Neighbor in Need')],
                          validators=[DataRequired()])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    submit = SubmitField('Register')

class TaskRequestForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(max=100)])
    category = SelectField('Category', 
                         choices=[
                             ('household', 'Household Tasks'),
                             ('errands', 'Errands'),
                             ('companionship', 'Companionship'),
                             ('outdoor', 'Outdoor Work'),
                             ('technology', 'Technology Help'),
                             ('childcare', 'Childcare Assistance'),
                             ('other', 'Other')
                         ],
                         validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    preferred_time = StringField('Preferred Time/Date', validators=[DataRequired()])
    submit = SubmitField('Submit Request')

class VolunteerProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    skills = TextAreaField('Skills (separate with commas)', validators=[Optional()])
    availability = TextAreaField('Availability', validators=[Optional()])
    bio = TextAreaField('About Me', validators=[Optional()])
    submit = SubmitField('Update Profile')

class FeedbackForm(FlaskForm):
    rating = RadioField('Rating', 
                      choices=[(1, '1 - Poor'), (2, '2 - Fair'), (3, '3 - Good'), 
                              (4, '4 - Very Good'), (5, '5 - Excellent')],
                      validators=[DataRequired()], coerce=int)
    comments = TextAreaField('Comments')
    submit = SubmitField('Submit Feedback')
