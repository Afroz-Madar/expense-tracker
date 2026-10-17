from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# hi hello
class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.now().date)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'date': self.date.isoformat(),
            'category': self.category,
            'amount': self.amount,
            'description': self.description
        }

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    today = datetime.now().date()
    today_expenses = Expense.query.filter_by(date=today).all()
    today_total = sum(e.amount for e in today_expenses)
    categories = ['Food', 'Transport', 'Entertainment', 'Shopping', 'Bills', 'Health', 'Other']
    expenses_json = [e.to_dict() for e in today_expenses]
    return render_template('index.html',
                         expenses=today_expenses,
                         expenses_json=expenses_json,
                         today_total=today_total,
                         categories=categories,
                         today=today)

@app.route('/api/add-expense', methods=['POST'])
def add_expense():
    try:
        data = request.json
        date_str = data.get('date', datetime.now().date().isoformat())
        expense = Expense(
            date=datetime.fromisoformat(date_str).date(),
            category=data.get('category'),
            amount=float(data.get('amount')),
            description=data.get('description', '')
        )
        db.session.add(expense)
        db.session.commit()
        return jsonify({'success': True, 'expense': expense.to_dict()}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/delete-expense/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    try:
        expense = Expense.query.get(expense_id)
        if expense:
            db.session.delete(expense)
            db.session.commit()
            return jsonify({'success': True}), 200
        return jsonify({'success': False, 'error': 'Expense not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/daily/<date_str>')
def daily_view(date_str):
    try:
        date_obj = datetime.fromisoformat(date_str).date()
        expenses = Expense.query.filter_by(date=date_obj).all()
        daily_total = sum(e.amount for e in expenses)
        categories = ['Food', 'Transport', 'Entertainment', 'Shopping', 'Bills', 'Health', 'Other']
        return render_template('daily.html',
                             expenses=expenses,
                             daily_total=daily_total,
                             current_date=date_obj,
                             categories=categories)
    except Exception as e:
        return str(e), 400

@app.route('/monthly')
def monthly_report():
    today = datetime.now().date()
    first_day = today.replace(day=1)
    expenses = Expense.query.filter(
        Expense.date >= first_day,
        Expense.date <= today
    ).all()
    category_totals = {}
    for expense in expenses:
        if expense.category not in category_totals:
            category_totals[expense.category] = 0
        category_totals[expense.category] += expense.amount
    monthly_total = sum(e.amount for e in expenses)
    daily_average = monthly_total / today.day if today.day > 0 else 0
    expenses_json = [e.to_dict() for e in expenses]
    return render_template('monthly.html',
                         expenses=expenses,
                         expenses_json=expenses_json,
                         category_totals=category_totals,
                         monthly_total=monthly_total,
                         daily_average=daily_average,
                         current_month=first_day.strftime('%B %Y'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)
