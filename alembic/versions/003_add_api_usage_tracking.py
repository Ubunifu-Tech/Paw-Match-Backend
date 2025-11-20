"""Add API usage tracking

Revision ID: 003
Revises: 002
Create Date: 2025-11-19 15:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create api_usage table
    op.create_table(
        'api_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('api_type', sa.String(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('month', sa.String(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('last_used', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('ix_api_usage_user_id', 'api_usage', ['user_id'])
    op.create_index('ix_api_usage_api_type', 'api_usage', ['api_type'])
    op.create_index('ix_api_usage_month', 'api_usage', ['month'])
    op.create_index('idx_user_api_month', 'api_usage', ['user_id', 'api_type', 'month'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_user_api_month', table_name='api_usage')
    op.drop_index('ix_api_usage_month', table_name='api_usage')
    op.drop_index('ix_api_usage_api_type', table_name='api_usage')
    op.drop_index('ix_api_usage_user_id', table_name='api_usage')
    
    # Drop table
    op.drop_table('api_usage')
