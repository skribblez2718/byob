"""Set sequential display_order for existing projects

Revision ID: 160b723cb382
Revises: 000000000001
Create Date: 2025-09-07 09:45:21.606290

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '160b723cb382'
down_revision = '000000000001'
branch_labels = None
depends_on = None


def upgrade():
    # Update existing projects to have sequential display_order values
    # This ensures proper ordering for projects that may have been created
    # before the display_order field was properly utilized
    
    connection = op.get_bind()
    
    # Get all users who have projects
    users_with_projects = connection.execute(
        sa.text("SELECT DISTINCT user_id FROM projects ORDER BY user_id")
    ).fetchall()
    
    # For each user, set sequential display_order values based on creation date
    for user_row in users_with_projects:
        user_id = user_row[0]
        
        # Get projects for this user ordered by created_at, then id
        projects = connection.execute(
            sa.text("""
                SELECT id FROM projects 
                WHERE user_id = :user_id 
                ORDER BY created_at ASC, id ASC
            """),
            {"user_id": user_id}
        ).fetchall()
        
        # Update each project with sequential display_order
        for index, project_row in enumerate(projects):
            project_id = project_row[0]
            connection.execute(
                sa.text("""
                    UPDATE projects 
                    SET display_order = :display_order 
                    WHERE id = :project_id
                """),
                {"display_order": index, "project_id": project_id}
            )


def downgrade():
    # Reset all display_order values to 0
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE projects SET display_order = 0")
    )
