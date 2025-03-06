from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)

# Configuration for database and secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///calorie_counter.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)  # Secure secret key for production

# Initialize the database
db = SQLAlchemy(app)

# Models for the database
class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_item = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(20), nullable=False)
    protein = db.Column(db.Float, nullable=False)
    sugars = db.Column(db.Float, nullable=False)
    fats = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    kcal = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<FoodItem {self.food_item}>"

class DailyLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    quantity_consumed = db.Column(db.String(50), nullable=False)
    protein_consumed = db.Column(db.Float, nullable=False)
    sugars_consumed = db.Column(db.Float, nullable=False)
    fats_consumed = db.Column(db.Float, nullable=False)
    carbs_consumed = db.Column(db.Float, nullable=False)
    total_calories = db.Column(db.Float, nullable=False)

    food_item = db.relationship('FoodItem', backref=db.backref('daily_logs', lazy=True))

    def __repr__(self):
        return f"<DailyLog {self.food_item.food_item} - {self.date}>"

# Helper function to parse quantities
def parse_quantity(quantity_str):
    # Remove non-numeric characters (such as 'g', 'nos', etc.)
    numeric_value = ''.join(filter(str.isdigit, quantity_str))
    return float(numeric_value)

# Create the tables in the database
with app.app_context():
    db.create_all()

# Seed the food items into the database (if not already present)
def seed_food_items():
    food_items = [
        {"food_item": "Egg", "quantity": "1", "unit": "Nos", "protein": 6, "sugars": 0.6, "fats": 5, "carbs": 0.6, "kcal": 75},
        {"food_item": "Soya Chunks", "quantity": "50", "unit": "gm", "protein": 20, "sugars": 0, "fats": 0.4, "carbs": 17, "kcal": 170},
        # Add other food items similarly...
    ]

    # Insert food items if they don't already exist
    for food in food_items:
        if not FoodItem.query.filter_by(food_item=food['food_item']).first():
            new_food_item = FoodItem(**food)
            db.session.add(new_food_item)

    db.session.commit()

# Seed the data
with app.app_context():
    seed_food_items()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_food_item', methods=['GET', 'POST'])
def add_food_item():
    if request.method == 'POST':
        food_item = request.form['food_item']
        quantity = request.form['quantity']
        unit = request.form['unit']
        protein = float(request.form['protein'])
        sugars = float(request.form['sugars'])
        fats = float(request.form['fats'])
        carbs = float(request.form['carbs'])
        kcal = float(request.form['kcal'])

        new_food_item = FoodItem(food_item=food_item, quantity=quantity, unit=unit, protein=protein, sugars=sugars, fats=fats, carbs=carbs, kcal=kcal)
        db.session.add(new_food_item)
        db.session.commit()

        flash('Food item added successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_food_item.html')

@app.route('/log_food_item', methods=['GET', 'POST'])
def log_food_item():
    food_items = FoodItem.query.all()
    if request.method == 'POST':
        food_item_id = request.form['food_item']
        quantity_consumed = request.form['quantity_consumed']
        date = request.form['date']
        
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'error')
            return redirect(url_for('log_food_item'))

        selected_food_item = FoodItem.query.get(food_item_id)
        if not selected_food_item:
            flash('Food item not found.', 'error')
            return redirect(url_for('log_food_item'))

        quantity_ratio = round(parse_quantity(quantity_consumed) / parse_quantity(selected_food_item.quantity), 2)
        
        protein_consumed = selected_food_item.protein * quantity_ratio
        sugars_consumed = selected_food_item.sugars * quantity_ratio
        fats_consumed = selected_food_item.fats * quantity_ratio
        carbs_consumed = selected_food_item.carbs * quantity_ratio
        total_calories = selected_food_item.kcal * quantity_ratio

        new_log = DailyLog(
            food_item_id=food_item_id,
            quantity_consumed=quantity_consumed,
            date=date_obj,
            protein_consumed=protein_consumed,
            sugars_consumed=sugars_consumed,
            fats_consumed=fats_consumed,
            carbs_consumed=carbs_consumed,
            total_calories=total_calories
        )
        db.session.add(new_log)
        db.session.commit()

        flash('Food log added successfully!', 'success')
        return redirect(url_for('view_log'))

    return render_template('log_food_item.html', food_items=food_items)

@app.route('/edit_log/<int:log_id>', methods=['GET', 'POST'])
def edit_log(log_id):
    log = DailyLog.query.get_or_404(log_id)
    if request.method == 'POST':
        new_quantity = request.form['quantity_consumed']
        selected_food_item = log.food_item

        quantity_ratio = round(parse_quantity(new_quantity) / parse_quantity(selected_food_item.quantity),2)

        log.quantity_consumed = new_quantity
        log.protein_consumed = round(selected_food_item.protein * quantity_ratio, 2)
        log.sugars_consumed = round(selected_food_item.sugars * quantity_ratio, 2)
        log.fats_consumed = round(selected_food_item.fats * quantity_ratio,2)
        log.carbs_consumed = round(selected_food_item.carbs * quantity_ratio,2)
        log.total_calories = round(selected_food_item.kcal * quantity_ratio, 2)

        db.session.commit()

        flash('Food log updated successfully!', 'success')
        return redirect(url_for('view_log'))
    
    return render_template('edit_log.html', log=log)

@app.route('/delete_log/<int:log_id>', methods=['GET'])
def delete_log(log_id):
    log = DailyLog.query.get_or_404(log_id)
    db.session.delete(log)
    db.session.commit()
    flash('Food log deleted successfully!', 'success')
    return redirect(url_for('view_log'))

@app.route('/view_log')
def view_log():
    # Assuming you have a model for daily logs and each log has total_calories and protein_consumed
    logs = DailyLog.query.all()
    
    # Group logs by date
    daily_logs = {}
    for log in logs:
        log_date = log.date
        if log_date not in daily_logs:
            daily_logs[log_date] = {'logs': [], 'total_calories': 0, 'total_protein': 0}
        
        daily_logs[log_date]['logs'].append(log)
        daily_logs[log_date]['total_calories'] += log.total_calories
        daily_logs[log_date]['total_protein'] += log.protein_consumed
    
    # Convert to a list to pass to the template (sorting by date)
    daily_logs = [
        {'date': date, 'logs': data['logs'], 'total_calories': data['total_calories'], 'total_protein': data['total_protein']}
        for date, data in sorted(daily_logs.items())
    ]
    
    return render_template('view_log.html', daily_logs=daily_logs)

if __name__ == '__main__':
    app.run(debug=True)