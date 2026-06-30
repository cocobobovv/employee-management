# -*- coding: utf-8 -*-
"""
数据库模型 — 员工信息表
"""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Enum as SAEnum

db = SQLAlchemy()


class Employee(db.Model):
    """员工信息模型"""
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    gender = db.Column(SAEnum('男', '女', name='gender_type'),
                       nullable=False, comment='性别')
    age = db.Column(db.Integer, nullable=False, comment='年龄')
    birthplace = db.Column(db.String(100), nullable=False, comment='出生地')
    department = db.Column(db.String(50), nullable=True, comment='部门')
    position = db.Column(db.String(50), nullable=True, comment='职位')
    phone = db.Column(db.String(20), nullable=True, comment='联系电话')
    email = db.Column(db.String(100), nullable=True, comment='电子邮箱')
    hire_date = db.Column(db.Date, nullable=True, comment='入职日期')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           comment='创建时间')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc),
                           comment='更新时间')

    __table_args__ = (
        CheckConstraint('age >= 16 AND age <= 100', name='ck_employee_age_range'),
    )

    def to_dict(self):
        """转换为字典（用于 API 响应）"""
        return {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'age': self.age,
            'birthplace': self.birthplace,
            'department': self.department,
            'position': self.position,
            'phone': self.phone,
            'email': self.email,
            'hire_date': self.hire_date.strftime('%Y-%m-%d') if self.hire_date else '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else '',
        }

    def __repr__(self):
        return f'<Employee {self.id}: {self.name}>'
