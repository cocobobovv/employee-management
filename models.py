# -*- coding: utf-8 -*-
"""
数据库模型 — 员工信息表 & 用户表
"""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """管理员用户模型"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, comment='用户名')
    password_hash = db.Column(db.String(256), nullable=False, comment='密码哈希')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           comment='创建时间')

    def set_password(self, password: str) -> None:
        """设置密码（自动加盐哈希）"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.id}: {self.username}>'


class Employee(db.Model):
    """员工信息模型"""
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    gender = db.Column(db.String(6), nullable=False, comment='性别')
    age = db.Column(db.Integer, nullable=True, comment='年龄')
    birthplace = db.Column(db.String(100), nullable=True, comment='出生地')
    department = db.Column(db.String(50), nullable=True, comment='部门')
    position = db.Column(db.String(100), nullable=True, comment='岗位/职务')
    team_station = db.Column(db.String(100), nullable=True, comment='现班组/井站')
    work_content = db.Column(db.Text, nullable=True, comment='分管工作内容')
    remarks = db.Column(db.Text, nullable=True, comment='备注')
    phone = db.Column(db.String(20), nullable=True, comment='联系电话')
    email = db.Column(db.String(100), nullable=True, comment='电子邮箱')
    hire_date = db.Column(db.Date, nullable=True, comment='入职日期')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           comment='创建时间')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc),
                           comment='更新时间')

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
            'team_station': self.team_station,
            'work_content': self.work_content,
            'remarks': self.remarks,
            'phone': self.phone,
            'email': self.email,
            'hire_date': self.hire_date.strftime('%Y-%m-%d') if self.hire_date else '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else '',
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else '',
        }

    def __repr__(self):
        return f'<Employee {self.id}: {self.name}>'
