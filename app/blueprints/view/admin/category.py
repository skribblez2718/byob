from __future__ import annotations

from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user

from app.decorators import admin_required, mfa_required
from app.forms import CategoryForm
from app.forms.categories import DeleteCategoryForm
from app.repositories.blog import (
    create_category,
    list_categories,
    get_category_by_id,
    get_category_by_hex_id,
    update_category,
    delete_category,
)
from app.utils.slug import slugify

from app.blueprints.admin import bp


@bp.route("/categories")
@admin_required
@mfa_required
def categories_list():
    cats = list_categories()
    delete_form = DeleteCategoryForm()
    return render_template(
        "admin/categories_list.html",
        title="Manage Categories",
        categories=cats,
        delete_form=delete_form,
    )


@bp.route("/categories/new", methods=["GET", "POST"])
@admin_required
@mfa_required
def category_new():
    """HTML form to create new category"""
    form = CategoryForm()

    if form.validate_on_submit():
        try:
            new_category = create_category(
                name=form.name.data,
                slug=slugify(form.name.data),
                description=form.description.data or "",
                display_order=0,
            )
            flash(f'Category "{new_category.name}" created successfully!', "success")
            return redirect(url_for("admin.categories_list"))
        except Exception as e:
            flash(f"Error creating category: {str(e)}", "error")

    return render_template(
        "admin/category_form.html", form=form, title="Add New Category"
    )


@bp.route("/categories/<string:category_hex_id>/edit", methods=["GET", "POST"])
@admin_required
@mfa_required
def category_edit(category_hex_id: str):
    cat = get_category_by_hex_id(category_hex_id)
    if not cat:
        flash("Category not found.", "error")
        return redirect(url_for("admin.categories_list"))

    form = CategoryForm(obj=cat)
    if form.validate_on_submit():
        try:
            update_category(
                cat,
                name=form.name.data,
                slug=slugify(form.name.data),
                description=form.description.data or "",
                display_order=cat.display_order or 0,
            )
            flash("Category updated.", "success")
            return redirect(url_for("admin.categories_list"))
        except ValueError as e:
            if str(e) == "slug_conflict":
                flash("A category with this name already exists.", "error")
            else:
                flash(f"Error updating category: {str(e)}", "error")

    return render_template(
        "admin/category_form.html", form=form, title=f"Edit Category: {cat.name}"
    )


@bp.post("/categories/<string:category_hex_id>/delete", endpoint="category_delete_view")
@admin_required
@mfa_required
def category_delete_view(category_hex_id: str):
    form = DeleteCategoryForm()
    if form.validate_on_submit():
        cat = get_category_by_hex_id(category_hex_id)
        if not cat:
            flash("Category not found.", "error")
            return redirect(url_for("admin.categories_list"))
        delete_category(cat)
        flash("Category deleted.", "success")
        return redirect(url_for("admin.categories_list"))
    flash("Invalid delete request.", "error")
    return redirect(url_for("admin.categories_list"))
