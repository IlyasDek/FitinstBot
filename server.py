from flask import Flask, request, jsonify
from database.models import WorkoutModel, DietModel

app = Flask(__name__)


@app.route('/process_data', methods=['POST'])
def process_data():
    data = request.json
    if not data or 'type' not in data or 'data' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    if data['type'] == 'workout':
        result = WorkoutModel.process(data['data'])
    elif data['type'] == 'diet':
        result = DietModel.process(data['data'])
    elif data['type'] == 'both':
        workout_result = WorkoutModel.process(data['data'])
        diet_result = DietModel.process(data['data'])
        result = {'workout': workout_result, 'diet': diet_result}
    else:
        result = {'error': 'Invalid data type'}

    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)
