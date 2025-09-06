from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, TextAreaField, FieldList, FormField, BooleanField
from wtforms.validators import DataRequired, Length, Optional


class SkillItemForm(FlaskForm):
    skill_title = StringField('Skill Title', validators=[DataRequired(), Length(max=120)])
    skill_description = TextAreaField('Skill Description', validators=[DataRequired()])
    delete = BooleanField('Delete', default=False)


class WorkAccomplishmentForm(FlaskForm):
    accomplishment_text = StringField('Accomplishment', validators=[DataRequired()])
    delete = BooleanField('Delete', default=False)


class WorkHistoryItemForm(FlaskForm):
    work_history_image_url = StringField('Current Image')
    work_history_image = FileField('Company/Image (PNG/JPEG/WEBP)', validators=[Optional()])
    remove_image = BooleanField('Remove Image')
    work_history_company_name = StringField('Company Name', validators=[DataRequired(), Length(max=200)])
    work_history_dates = StringField('Dates', validators=[DataRequired(), Length(max=120)])
    work_history_role = StringField('Role/Title', validators=[DataRequired(), Length(max=200)])
    work_history_role_description = TextAreaField('Role Description', validators=[Optional()])
    accomplishments = FieldList(FormField(WorkAccomplishmentForm), min_entries=0)
    delete = BooleanField('Delete', default=False)


class CertificationItemForm(FlaskForm):
    image_url = StringField('Current Image')
    image = FileField('Certification Image (PNG/JPEG/WEBP)', validators=[Optional()])
    remove_image = BooleanField('Remove Image')
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    delete = BooleanField('Delete', default=False)


class ProfessionalDevelopmentItemForm(FlaskForm):
    image_url = StringField('Current Image')
    image = FileField('Image (PNG/JPEG/WEBP)', validators=[Optional()])
    remove_image = BooleanField('Remove Image')
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    delete = BooleanField('Delete', default=False)


class EducationItemForm(FlaskForm):
    image_url = StringField('Current Image')
    image = FileField('Education Image (PNG/JPEG/WEBP)', validators=[Optional()])
    remove_image = BooleanField('Remove Image')
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[Optional()])
    delete = BooleanField('Delete', default=False)


class ResumeForm(FlaskForm):
    skills = FieldList(FormField(SkillItemForm), min_entries=0)
    work_history = FieldList(FormField(WorkHistoryItemForm), min_entries=0)
    certifications = FieldList(FormField(CertificationItemForm), min_entries=0)
    professional_development = FieldList(FormField(ProfessionalDevelopmentItemForm), min_entries=0)
    education = FieldList(FormField(EducationItemForm), min_entries=0)
    submit = SubmitField('Save Resume')
