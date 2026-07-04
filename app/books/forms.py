"""
app/books/forms.py - Book & Category Forms
Save at: LMS/app/books/forms.py
"""

import os
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, TextAreaField, IntegerField, SelectField,
                     SubmitField, BooleanField)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, ValidationError
from app.models.book import Book


class BookForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=255)])
    author = StringField('Author', validators=[DataRequired(), Length(max=255)])
    isbn = StringField('ISBN', validators=[Optional(), Length(max=20)])
    publisher = StringField('Publisher', validators=[Optional(), Length(max=150)])
    publication_year = IntegerField('Publication Year',
                                    validators=[Optional(), NumberRange(min=1000, max=2100)])
    edition = StringField('Edition', validators=[Optional(), Length(max=50)])
    language = StringField('Language', validators=[Optional(), Length(max=50)])
    pages = IntegerField('Number of Pages', validators=[Optional(), NumberRange(min=1)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=2000)])
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    barcode = StringField('Barcode', validators=[Optional(), Length(max=50)])
    shelf_location = StringField('Shelf Location', validators=[Optional(), Length(max=50)])
    total_copies = IntegerField('Total Copies',
                                validators=[DataRequired(), NumberRange(min=1, max=999)])
    cover_image = FileField('Cover Image',
                            validators=[Optional(),
                                        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'],
                                                    'Images only!')])
    is_active = BooleanField('Active / Available', default=True)
    submit = SubmitField('Save Book')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models.book import Category
        cats = Category.query.order_by('name').all()
        self.category_id.choices = [(0, '— Select Category —')] + [
            (c.id, c.name) for c in cats
        ]

    def validate_isbn(self, field):
        if field.data:
            existing = Book.query.filter_by(isbn=field.data).first()
            # Allow same ISBN when editing (obj_id passed via meta)
            if existing and str(existing.id) != str(self.meta.get('obj_id', '')):
                raise ValidationError('A book with this ISBN already exists.')


class CategoryForm(FlaskForm):
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Save Category')


class BookSearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    category = SelectField('Category', coerce=int, validators=[Optional()])
    availability = SelectField('Availability', choices=[
        (0, 'All'), (1, 'Available Only'), (2, 'Borrowed / Unavailable')
    ], coerce=int, validators=[Optional()])
    submit = SubmitField('Search')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.models.book import Category
        cats = Category.query.order_by('name').all()
        self.category.choices = [(0, 'All Categories')] + [(c.id, c.name) for c in cats]
