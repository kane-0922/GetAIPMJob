from coze_coding_dev_sdk.database import Base

from typing import Optional
import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Double, Integer, Numeric, PrimaryKeyConstraint, Table, Text, text, String, Index
from sqlalchemy.dialects.postgresql import JSON, OID
from sqlalchemy.orm import Mapped, mapped_column

class HealthCheck(Base):
    __tablename__ = 'health_check'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='health_check_pkey'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True), server_default=text('now()'))


class UserProfile(Base):
    """用户画像表 - 持久化存储求职者的个人信息、技能评估、学习进度等"""
    __tablename__ = 'user_profiles'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, comment="会话标识，用于关联同一用户的多次对话")
    name: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, comment="用户姓名")
    identity_type: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, comment="身份类型: intern/campus/experienced")
    education: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="教育背景: {degree, school, major, graduation_year}")
    target_positions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="目标岗位列表")
    skills_mastered: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="已掌握技能列表")
    skills_to_improve: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="待提升技能列表")
    resume_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="解析后的简历结构化数据")
    learning_progress: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, comment="学习进度: {topics_studied, topics_pending}")
    interview_history: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, comment="面试历史记录")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="Agent观察备注")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=text('now()'), nullable=False)
    updated_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), server_default=text('now()'), nullable=True)

    __table_args__ = (
        PrimaryKeyConstraint('id', name='user_profiles_pkey'),
        Index('user_profiles_session_id_idx', 'session_id'),
        Index('user_profiles_identity_type_idx', 'identity_type'),
    )


t_pg_stat_statements = Table(
    'pg_stat_statements', Base.metadata,
    Column('userid', OID),
    Column('dbid', OID),
    Column('toplevel', Boolean),
    Column('queryid', BigInteger),
    Column('query', Text),
    Column('plans', BigInteger),
    Column('total_plan_time', Double(53)),
    Column('min_plan_time', Double(53)),
    Column('max_plan_time', Double(53)),
    Column('mean_plan_time', Double(53)),
    Column('stddev_plan_time', Double(53)),
    Column('calls', BigInteger),
    Column('total_exec_time', Double(53)),
    Column('min_exec_time', Double(53)),
    Column('max_exec_time', Double(53)),
    Column('mean_exec_time', Double(53)),
    Column('stddev_exec_time', Double(53)),
    Column('rows', BigInteger),
    Column('shared_blks_hit', BigInteger),
    Column('shared_blks_read', BigInteger),
    Column('shared_blks_dirtied', BigInteger),
    Column('shared_blks_written', BigInteger),
    Column('local_blks_hit', BigInteger),
    Column('local_blks_read', BigInteger),
    Column('local_blks_dirtied', BigInteger),
    Column('local_blks_written', BigInteger),
    Column('temp_blks_read', BigInteger),
    Column('temp_blks_written', BigInteger),
    Column('shared_blk_read_time', Double(53)),
    Column('shared_blk_write_time', Double(53)),
    Column('local_blk_read_time', Double(53)),
    Column('local_blk_write_time', Double(53)),
    Column('temp_blk_read_time', Double(53)),
    Column('temp_blk_write_time', Double(53)),
    Column('wal_records', BigInteger),
    Column('wal_fpi', BigInteger),
    Column('wal_bytes', Numeric),
    Column('jit_functions', BigInteger),
    Column('jit_generation_time', Double(53)),
    Column('jit_inlining_count', BigInteger),
    Column('jit_inlining_time', Double(53)),
    Column('jit_optimization_count', BigInteger),
    Column('jit_optimization_time', Double(53)),
    Column('jit_emission_count', BigInteger),
    Column('jit_emission_time', Double(53)),
    Column('jit_deform_count', BigInteger),
    Column('jit_deform_time', Double(53)),
    Column('stats_since', DateTime(True)),
    Column('minmax_stats_since', DateTime(True))
)


t_pg_stat_statements_info = Table(
    'pg_stat_statements_info', Base.metadata,
    Column('dealloc', BigInteger),
    Column('stats_reset', DateTime(True))
)
