from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, HiddenField
from wtforms.validators import DataRequired, Length, Optional


class CategoryForm(FlaskForm):
    name = StringField(
        'Category Name',
        validators=[
            DataRequired(message='Category name is required'),
            Length(min=1, max=100, message='Category name must be between 1 and 100 characters')
        ],
        render_kw={'placeholder': 'Enter category name'}
    )
    description = TextAreaField(
        'Description',
        validators=[
            Optional(),
            Length(max=500, message='Description must be less than 500 characters')
        ],
        render_kw={'placeholder': 'Optional category description', 'rows': 3}
    )
    submit = SubmitField('Save Category')


class DeleteCategoryForm(FlaskForm):
    category_id = HiddenField()
    submit = SubmitField('Delete')
