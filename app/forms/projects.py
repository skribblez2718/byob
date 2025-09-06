from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, TextAreaField, FieldList, FormField, BooleanField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, URL


class ProjectItemForm(FlaskForm):
    class Meta:
        csrf = False 
    project_image_url = StringField('Current Image')
    project_image = FileField('Project Image (PNG/JPEG/WEBP)', validators=[Optional()])
    remove_image = BooleanField('Remove Image')
    project_title = StringField('Project Title', validators=[DataRequired(), Length(max=200)])
    project_description = TextAreaField('Project Description', validators=[Optional()])
    project_url = StringField('Project URL', validators=[Optional(), URL()])
    delete = BooleanField('Delete', default=False)


class ProjectsForm(FlaskForm):
    projects = FieldList(FormField(ProjectItemForm), min_entries=0)
    submit = SubmitField('Save Projects')


class DeleteProjectForm(FlaskForm):
    project_id = HiddenField()
    submit = SubmitField('Delete')
