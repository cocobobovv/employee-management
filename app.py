# -*- coding: utf-8 -*-
"""
员工管理系统 — Flask 主应用
功能：CRUD、搜索筛选、数据导出、RESTful API
"""
import csv
import io
import os
import re
from datetime import date, datetime
from typing import Optional

from flask import (Flask, render_template, request, redirect,
                   url_for, flash, jsonify, send_file, Response)
from flask_wtf.csrf import CSRFProtect
from openpyxl import Workbook

from models import db, Employee
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get(
    'SECRET_KEY',
    'please-set-secret-key-in-production'
)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employees.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
csrf = CSRFProtect(app)


# ══════════════════════════════════════════════
#  Web 页面路由
# ══════════════════════════════════════════════

@app.route('/')
def index() -> str:
    """员工列表首页，支持搜索和筛选"""
    search_query: str = request.args.get('q', '').strip()
    gender_filter: str = request.args.get('gender', '').strip()
    dept_filter: str = request.args.get('department', '').strip()
    page: int = request.args.get('page', 1, type=int)
    per_page: int = 20

    query = Employee.query

    if search_query:
        query = query.filter(
            Employee.name.contains(search_query) |
            Employee.birthplace.contains(search_query) |
            Employee.department.contains(search_query) |
            Employee.position.contains(search_query)
        )

    if gender_filter:
        query = query.filter(Employee.gender == gender_filter)

    if dept_filter:
        query = query.filter(Employee.department == dept_filter)

    pagination = query.order_by(Employee.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    employees = pagination.items

    # 获取所有部门（用于筛选下拉框）
    departments = db.session.query(Employee.department).distinct().all()
    departments = sorted([d[0] for d in departments if d[0]])

    return render_template(
        'index.html',
        employees=employees,
        pagination=pagination,
        search_query=search_query,
        gender_filter=gender_filter,
        dept_filter=dept_filter,
        departments=departments
    )


@app.route('/add', methods=['GET', 'POST'])
def add() -> str:
    """新增员工"""
    if request.method == 'POST':
        valid: bool
        errors: dict
        valid, errors = _validate_employee_data(request.form)
        if not valid:
            for field, msg in errors.items():
                flash(f'❌ {msg}', 'danger')
            return render_template('add.html')

        try:
            hire_date, date_err = _parse_date(request.form.get('hire_date'))
            if date_err:
                flash(f'❌ {date_err}', 'danger')
                return render_template('add.html')

            employee = Employee(
                name=request.form['name'].strip(),
                gender=request.form['gender'].strip(),
                age=int(request.form['age']),
                birthplace=request.form['birthplace'].strip(),
                department=request.form.get('department', '').strip(),
                position=request.form.get('position', '').strip(),
                phone=request.form.get('phone', '').strip(),
                email=request.form.get('email', '').strip(),
                hire_date=hire_date,
            )
            db.session.add(employee)
            db.session.commit()
            flash('✅ 员工添加成功！', 'success')
            return redirect(url_for('index'))
        except (ValueError, SQLAlchemyError) as e:
            db.session.rollback()
            flash(f'❌ 添加失败：{str(e)}', 'danger')

    return render_template('add.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id: int) -> str:
    """编辑员工信息"""
    employee = Employee.query.get_or_404(id)

    if request.method == 'POST':
        valid, errors = _validate_employee_data(request.form)
        if not valid:
            for field, msg in errors.items():
                flash(f'❌ {msg}', 'danger')
            return render_template('edit.html', employee=employee)

        try:
            employee.name = request.form['name'].strip()
            employee.gender = request.form['gender'].strip()
            employee.age = int(request.form['age'])
            employee.birthplace = request.form['birthplace'].strip()
            employee.department = request.form.get('department', '').strip()
            employee.position = request.form.get('position', '').strip()
            employee.phone = request.form.get('phone', '').strip()
            employee.email = request.form.get('email', '').strip()
            hire_date, date_err = _parse_date(request.form.get('hire_date'))
            if date_err:
                flash(f'❌ {date_err}', 'danger')
                return render_template('edit.html', employee=employee)
            employee.hire_date = hire_date
            db.session.commit()
            flash('✅ 员工信息已更新！', 'success')
            return redirect(url_for('index'))
        except (ValueError, SQLAlchemyError) as e:
            db.session.rollback()
            flash(f'❌ 更新失败：{str(e)}', 'danger')

    return render_template('edit.html', employee=employee)


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id: int) -> str:
    """删除员工"""
    employee = Employee.query.get_or_404(id)
    try:
        db.session.delete(employee)
        db.session.commit()
        flash('✅ 员工已删除！', 'success')
    except (ValueError, SQLAlchemyError) as e:
        flash(f'❌ 删除失败：{str(e)}', 'danger')
    return redirect(url_for('index'))


@app.route('/export/csv')
def export_csv() -> Response:
    """导出员工数据为 CSV"""
    employees = Employee.query.order_by(Employee.id).all()
    output = io.StringIO()
    writer = csv.writer(output)

    # 表头
    writer.writerow(['编号', '姓名', '性别', '年龄', '出生地',
                     '部门', '职位', '电话', '邮箱', '入职日期'])

    for emp in employees:
        writer.writerow([
            emp.id, emp.name, emp.gender, emp.age, emp.birthplace,
            emp.department, emp.position, emp.phone, emp.email,
            emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else ''
        ])

    output.seek(0)
    return _send_csv_response(output, 'employees.csv')


@app.route('/export/excel')
def export_excel() -> Response:
    """导出员工数据为 Excel (.xlsx)"""
    employees = Employee.query.order_by(Employee.id).all()
    wb = Workbook()
    ws = wb.active
    ws.title = '员工信息'

    # 表头
    headers = ['编号', '姓名', '性别', '年龄', '出生地',
               '部门', '职位', '电话', '邮箱', '入职日期']
    ws.append(headers)

    for emp in employees:
        ws.append([
            emp.id, emp.name, emp.gender, emp.age, emp.birthplace,
            emp.department, emp.position, emp.phone, emp.email,
            emp.hire_date.strftime('%Y-%m-%d') if emp.hire_date else ''
        ])

    # 调整列宽
    for col in ws.columns:
        max_len = max(len(str(c.value or '')) for c in col)
        ws.column_dimensions[col[0].column_letter].width = max_len + 4

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='employees.xlsx'
    )


# ══════════════════════════════════════════════
#  RESTful API 路由
# ══════════════════════════════════════════════

@app.route('/api/employees', methods=['GET'])
def api_list() -> Response:
    """API: 获取员工列表（支持搜索）"""
    search = request.args.get('q', '').strip()
    query = Employee.query
    if search:
        query = query.filter(
            Employee.name.contains(search) |
            Employee.birthplace.contains(search) |
            Employee.department.contains(search)
        )
    employees = query.order_by(Employee.id.desc()).all()
    return jsonify({'code': 200, 'data': [e.to_dict() for e in employees]})


@app.route('/api/employees/<int:id>', methods=['GET'])
def api_detail(id: int) -> Response:
    """API: 获取单个员工信息"""
    employee = Employee.query.get_or_404(id)
    return jsonify({'code': 200, 'data': employee.to_dict()})


@app.route('/api/employees', methods=['POST'])
@csrf.exempt
def api_create() -> Response:
    """API: 新增员工"""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    required_fields = ['name', 'gender', 'age', 'birthplace']
    for field in required_fields:
        if field not in data:
            return jsonify({'code': 400, 'message': f'缺少必填字段: {field}'}), 400

    # 格式验证
    valid, errors = _validate_employee_data(data)
    if not valid:
        msg = '；'.join(errors.values())
        return jsonify({'code': 400, 'message': msg}), 400

    hire_date, date_err = _parse_date(data.get('hire_date'))
    if date_err and data.get('hire_date'):
        return jsonify({'code': 400, 'message': date_err}), 400

    try:
        employee = Employee(
            name=data['name'],
            gender=data['gender'],
            age=int(data['age']),
            birthplace=data['birthplace'],
            department=data.get('department', ''),
            position=data.get('position', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            hire_date=hire_date,
        )
        db.session.add(employee)
        db.session.commit()
        return jsonify({'code': 201, 'message': '创建成功', 'data': employee.to_dict()}), 201
    except (ValueError, SQLAlchemyError) as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'创建失败: {str(e)}'}), 500


@app.route('/api/employees/<int:id>', methods=['PUT'])
@csrf.exempt
def api_update(id: int) -> Response:
    """API: 更新员工信息"""
    employee = Employee.query.get_or_404(id)
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'code': 400, 'message': '请求体不能为空'}), 400

    try:
        # 验证提供的数据
        valid, errors = _validate_employee_data(data)
        if not valid:
            msg = '；'.join(errors.values())
            return jsonify({'code': 400, 'message': msg}), 400

        if 'name' in data:
            employee.name = data['name']
        if 'gender' in data:
            employee.gender = data['gender']
        if 'age' in data:
            employee.age = int(data['age'])
        if 'birthplace' in data:
            employee.birthplace = data['birthplace']
        if 'department' in data:
            employee.department = data['department']
        if 'position' in data:
            employee.position = data['position']
        if 'phone' in data:
            employee.phone = data['phone']
        if 'email' in data:
            employee.email = data['email']
        if 'hire_date' in data:
            hire_date, date_err = _parse_date(data['hire_date'])
            if date_err and data.get('hire_date'):
                return jsonify({'code': 400, 'message': date_err}), 400
            employee.hire_date = hire_date

        db.session.commit()
        return jsonify({'code': 200, 'message': '更新成功', 'data': employee.to_dict()})
    except (ValueError, SQLAlchemyError) as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'更新失败: {str(e)}'}), 500


@app.route('/api/employees/<int:id>', methods=['DELETE'])
@csrf.exempt
def api_delete(id: int) -> Response:
    """API: 删除员工"""
    employee = Employee.query.get_or_404(id)
    try:
        db.session.delete(employee)
        db.session.commit()
        return jsonify({'code': 200, 'message': '删除成功'})
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'删除失败: {str(e)}'}), 500


# ──────────────────────────────────────────────
#  数据验证
# ──────────────────────────────────────────────

def _validate_employee_data(data):
    """验证员工表单/API 数据，返回 (is_valid, errors_dict)

    data 是类字典对象（request.form 或 JSON dict）。
    errors 是 {字段名: 错误消息} 的字典。
    """
    errors = {}

    name = data.get('name', '').strip()
    if not name:
        errors['name'] = '姓名不能为空'
    elif len(name) > 50:
        errors['name'] = '姓名不能超过 50 个字符'

    gender = data.get('gender', '').strip()
    if not gender:
        errors['gender'] = '性别不能为空'
    elif gender not in ('男', '女'):
        errors['gender'] = '性别只能为「男」或「女」'

    age_raw = data.get('age', '')
    try:
        age = int(age_raw)
        if age < 16 or age > 100:
            errors['age'] = '年龄必须在 16 到 100 之间'
    except (ValueError, TypeError):
        errors['age'] = '年龄必须是有效数字'

    birthplace = data.get('birthplace', '').strip()
    if not birthplace:
        errors['birthplace'] = '出生地不能为空'
    elif len(birthplace) > 100:
        errors['birthplace'] = '出生地不能超过 100 个字符'

    phone = data.get('phone', '').strip()
    if phone and not _is_valid_phone(phone):
        errors['phone'] = '电话格式不正确（应为 11 位手机号或带区号座机）'

    email = data.get('email', '').strip()
    if email and not _is_valid_email(email):
        errors['email'] = '邮箱格式不正确'

    return len(errors) == 0, errors


def _is_valid_phone(phone: str) -> bool:
    """简单手机号/座机格式校验"""
    # 手机号：11 位数字，以 1 开头
    # 座机：区号-号码，如 010-88888888
    return bool(re.match(r'^1\d{10}$', phone) or
                re.match(r'^0\d{2,3}-?\d{7,8}$', phone))


def _is_valid_email(email: str) -> bool:
    """简单邮箱格式校验"""
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email))


# ──────────────────────────────────────────────
#  工具函数
# ──────────────────────────────────────────────

def _parse_date(date_str: Optional[str]) -> tuple[Optional[date], Optional[str]]:
    """解析日期字符串，返回 (date, error_message) 元组。

    解析成功时返回 (date_obj, None)；失败时返回 (None, '日期格式不正确')。
    """
    if not date_str or not date_str.strip():
        return None, None
    try:
        return datetime.strptime(date_str.strip(), '%Y-%m-%d').date(), None
    except ValueError:
        return None, '日期格式不正确（应为 YYYY-MM-DD）'


def _send_csv_response(output: io.StringIO, filename: str) -> Response:
    """将 CSV 字符串流作为附件响应返回"""
    output_bytes = io.BytesIO(output.getvalue().encode('utf-8-sig'))
    return Response(
        output_bytes.getvalue(),
        mimetype='text/csv; charset=utf-8-sig',
        headers={
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Type': 'text/csv; charset=utf-8-sig'
        }
    )


# ──────────────────────────────────────────────
#  统一错误处理器
# ──────────────────────────────────────────────

@app.errorhandler(404)
def not_found(e) -> tuple[str, int]:
    """404 页面"""
    return render_template('error.html', code=404, message='页面未找到'), 404


@app.errorhandler(500)
def server_error(e) -> tuple[str, int]:
    """500 页面"""
    return render_template('error.html', code=500, message='服务器内部错误'), 500


# ──────────────────────────────────────────────
#  CLI 命令
# ──────────────────────────────────────────────

@app.cli.command('init-db')
def init_db() -> None:
    """初始化数据库（创建所有表）"""
    db.create_all()
    print('✅ 数据库表已创建。')


# ──────────────────────────────────────────────
#  启动入口
# ──────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
