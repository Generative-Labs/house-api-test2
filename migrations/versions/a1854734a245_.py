"""empty message

Revision ID: a1854734a245
Revises: 
Create Date: 2021-04-20 12:36:11.266138

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1854734a245'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('play_table', sa.Column('share_id', sa.Text(), nullable=True))
    op.add_column('subscribers', sa.Column('status', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('subscribers', 'status')
    op.drop_column('play_table', 'share_id')
    # ### end Alembic commands ###