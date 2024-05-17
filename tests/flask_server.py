from flask import Flask, request, jsonify

app = Flask(__name__)

def add(a: float, b: float) -> float:
    """
    @brief 加法运算
    @param a 第一个操作数
    @param b 第二个操作数
    @return a和b的和
    """
    return a + b

def subtract(a: float, b: float) -> float:
    """
    @brief 减法运算
    @param a 第一个操作数
    @param b 第二个操作数
    @return a减去b的结果
    """
    return a - b

def multiply(a: float, b: float) -> float:
    """
    @brief 乘法运算
    @param a 第一个操作数
    @param b 第二个操作数
    @return a和b的积
    """
    return a * b

def divide(a: float, b: float) -> float:
    """
    @brief 除法运算
    @param a 第一个操作数
    @param b 第二个操作数
    @return a除以b的结果
    @note 如果b为0，将引发ZeroDivisionError
    """
    if b == 0:
        raise ZeroDivisionError("除数不能为零")
    return a / b

@app.route('/add', methods=['GET'])
def add_route():
    a = float(request.args.get('a'))
    b = float(request.args.get('b'))
    result = add(a, b)
    return jsonify(result=result)

@app.route('/subtract', methods=['GET'])
def subtract_route():
    a = float(request.args.get('a'))
    b = float(request.args.get('b'))
    result = subtract(a, b)
    return jsonify(result=result)

@app.route('/multiply', methods=['GET'])
def multiply_route():
    a = float(request.args.get('a'))
    b = float(request.args.get('b'))
    result = multiply(a, b)
    return jsonify(result=result)

@app.route('/divide', methods=['GET'])
def divide_route():
    a = float(request.args.get('a'))
    b = float(request.args.get('b'))
    try:
        result = divide(a, b)
    except ZeroDivisionError as e:
        return jsonify(error=str(e)), 400
    return jsonify(result=result)

if __name__ == '__main__':
    app.run(port=5645)
