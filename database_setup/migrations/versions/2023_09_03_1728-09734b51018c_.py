"""empty message

Revision ID: 09734b51018c
Revises: edc492faa8d0
Create Date: 2023-09-03 17:28:21.869967

"""

# revision identifiers, used by Alembic.
revision = '09734b51018c'
down_revision = 'edc492faa8d0'

from alembic import op
import sqlalchemy as sa
import sqlmodel


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('crc_expr_repeatlen_corr',
    sa.Column('repeat_id', sa.Integer(), nullable=True),
    sa.Column('gene_id', sa.Integer(), nullable=True),
    sa.Column('p_value', sa.Float(), nullable=False),
    sa.Column('p_value_corrected', sa.Float(), nullable=False),
    sa.Column('coefficient', sa.Float(), nullable=False),
    sa.Column('intercept', sa.Float(), nullable=False),
    sa.ForeignKeyConstraint(['gene_id'], ['genes.id'], ),
    sa.ForeignKeyConstraint(['repeat_id'], ['repeats.id'], ),
    sa.PrimaryKeyConstraint('gene_id', 'repeat_id'),
    )
    with op.batch_alter_table('crc_expr_repeatlen_corr', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_crc_expr_repeatlen_corr_coefficient'), ['coefficient'], unique=False)
        batch_op.create_index(batch_op.f('ix_crc_expr_repeatlen_corr_gene_id'), ['gene_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_crc_expr_repeatlen_corr_intercept'), ['intercept'], unique=False)
        batch_op.create_index(batch_op.f('ix_crc_expr_repeatlen_corr_p_value'), ['p_value'], unique=False)
        batch_op.create_index(batch_op.f('ix_crc_expr_repeatlen_corr_p_value_corrected'), ['p_value_corrected'], unique=False)
        batch_op.create_index(batch_op.f('ix_crc_expr_repeatlen_corr_repeat_id'), ['repeat_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('crc_expr_repeatlen_corr', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_crc_expr_repeatlen_corr_repeat_id'))
        batch_op.drop_index(batch_op.f('ix_crc_expr_repeatlen_corr_p_value_corrected'))
        batch_op.drop_index(batch_op.f('ix_crc_expr_repeatlen_corr_p_value'))
        batch_op.drop_index(batch_op.f('ix_crc_expr_repeatlen_corr_intercept'))
        batch_op.drop_index(batch_op.f('ix_crc_expr_repeatlen_corr_gene_id'))
        batch_op.drop_index(batch_op.f('ix_crc_expr_repeatlen_corr_coefficient'))

    op.drop_table('crc_expr_repeatlen_corr')
    # ### end Alembic commands ###