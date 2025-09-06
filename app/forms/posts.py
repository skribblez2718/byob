from __future__ import annotations

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    SubmitField,
    TextAreaField,
    SelectField,
    BooleanField,
    HiddenField,
    FieldList,
    FormField,
    IntegerField,
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from wtforms import Form


class ContentBlockForm(Form):
    """A single content block inside the blog post editor."""
    type = SelectField(
        'Type', choices=[('heading', 'Heading'), ('paragraph', 'Paragraph'), ('image', 'Image')], validators=[DataRequired()]
    )
    heading_level = SelectField(
        'Heading Level', choices=[('2', 'H2'), ('3', 'H3'), ('4', 'H4'), ('5', 'H5')], default='2'
    )
    text = TextAreaField('Text', render_kw={'rows': 3, 'class': 'form-control'})
    image = FileField(
        'Image',
        validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Only image files are allowed!')],
        render_kw={'class': 'form-control', 'accept': 'image/*'}
    )
    alt = StringField('Alt text', render_kw={'placeholder': 'Optional alt text', 'class': 'form-control'})
    existing_src = HiddenField('Existing Src')
    order = IntegerField('Order', default=0, validators=[NumberRange(min=0)])
    delete = BooleanField('Delete')


class BlogPostForm(FlaskForm):
    title = StringField(
        'Title',
        validators=[
            DataRequired(message='Title is required'),
            Length(min=1, max=200, message='Title must be between 1 and 200 characters')
        ],
        render_kw={'placeholder': 'Enter blog post title', 'class': 'form-control'}
    )
    category_id = SelectField(
        'Category',
        validators=[DataRequired(message='Category is required')],
        coerce=int,
        choices=[],  # Will be populated dynamically
        render_kw={'class': 'form-select'}
    )
    # Dynamic content blocks replace single content field
    content_blocks = FieldList(FormField(ContentBlockForm), min_entries=0)
    excerpt = TextAreaField(
        'Excerpt',
        validators=[
            DataRequired(message='Excerpt is required'),
            Length(min=1, max=300, message='Excerpt must be between 1 and 300 characters')
        ],
        render_kw={'placeholder': 'Short summary (required)', 'rows': 3, 'class': 'form-control'}
    )
    featured_image = FileField(
        'Featured Image',
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Only image files are allowed!')
        ],
        render_kw={'class': 'form-control', 'accept': 'image/*'}
    )
    # Hidden field to store post ID for editing
    post_id = HiddenField()
    submit = SubmitField('Save Post', render_kw={'class': 'btn btn-primary'})

    def validate(self, extra_validators=None):  # type: ignore[override]
        ok = super().validate(extra_validators=extra_validators)
        if not ok:
            return False
        # Per-block validations
        non_deleted_blocks = []
        for idx, entry in enumerate(self.content_blocks):
            b = entry.form
            if b.delete.data:
                continue
            non_deleted_blocks.append(entry)
            t = (b.type.data or '').strip()
            if t == 'heading':
                if not b.text.data or len(b.text.data.strip()) < 3:
                    entry.form.text.errors.append('Heading text must be at least 3 characters')
                    ok = False
            elif t == 'paragraph':
                if not b.text.data or len(b.text.data.strip()) < 10:
                    entry.form.text.errors.append('Paragraph must be at least 10 characters')
                    ok = False
            elif t == 'image':
                # Image field optional on edit; allow empty but if provided must pass FileAllowed (already handled)
                pass
            else:
                entry.form.type.errors.append('Invalid block type')
                ok = False
        # Must have at least one block
        if not non_deleted_blocks:
            self.content_blocks.errors.append('Add at least one content block')
            ok = False
        # Must include at least one paragraph
        has_paragraph = any((e.form.type.data == 'paragraph' and not e.form.delete.data) for e in self.content_blocks)
        if not has_paragraph:
            self.content_blocks.errors.append('At least one paragraph block is required')
            ok = False
        return ok


class DeletePostForm(FlaskForm):
    post_id = HiddenField()
    submit = SubmitField('Delete', render_kw={'class': 'btn btn-sm btn-danger'})
