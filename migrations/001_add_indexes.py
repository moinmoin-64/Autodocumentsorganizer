"""add_indexes_to_documents

Revision ID: 001
Create Date: 2024-11-30

Adds performance indexes to Document table
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '001_add_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add indexes to documents table for better performance"""
    
    # Single column indexes
    with op.batch_alter_table('documents') as batch_op:
        batch_op.create_index('ix_documents_filename', ['filename'])
        batch_op.create_index('ix_documents_category', ['category'])
        batch_op.create_index('ix_documents_subcategory', ['subcategory'])
        batch_op.create_index('ix_documents_date_document', ['date_document'])
        batch_op.create_index('ix_documents_date_added', ['date_added'])
        batch_op.create_index('ix_documents_content_hash', ['content_hash'])
    
    # Composite indexes for common queries
    op.create_index('idx_cat_date', 'documents', ['category', 'date_document'])
    op.create_index('idx_cat_added', 'documents', ['category', 'date_added'])
    op.create_index('idx_date_cat', 'documents', ['date_document', 'category'])


def downgrade():
    """Remove indexes"""
    
    # Drop composite indexes
    op.drop_index('idx_date_cat', table_name='documents')
    op.drop_index('idx_cat_added', table_name='documents')
    op.drop_index('idx_cat_date', table_name='documents')
    
    # Drop single column indexes
    with op.batch_alter_table('documents') as batch_op:
        batch_op.drop_index('ix_documents_content_hash')
        batch_op.drop_index('ix_documents_date_added')
        batch_op.drop_index('ix_documents_date_document')
        batch_op.drop_index('ix_documents_subcategory')
        batch_op.drop_index('ix_documents_category')
        batch_op.drop_index('ix_documents_filename')
