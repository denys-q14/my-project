def sum_values(digit1: int | float, digit2: int | float) -> int | float:
    """Повертає суму двох числових значень.

    Parameters:
        digit1 (int | float): Перше число.
        digit2 (int | float): Друге число.

    Returns:
        int | float: Сума digit1 і digit2.
    """
    return digit1 + digit2


def subtract_values(digit1: int | float, digit2: int | float) -> int | float:
    """Повертає різницю двох числових значень.

    Parameters:
        digit1 (int | float): Перше число.
        digit2 (int | float): Друге число.

    Returns:
        int | float: Різниця digit1 мінус digit2.
    """
    return digit1 - digit2


def multiply_values(digit1: int | float, digit2: int | float) -> int | float:
    """Повертає добуток двох числових значень.

    Parameters:
        digit1 (int | float): Перше число.
        digit2 (int | float): Друге число.

    Returns:
        int | float: Добуток digit1 і digit2.
    """
    return digit1 * digit2


def divide_values(digit1: int | float, digit2: int | float) -> float:
    """Повертає частку двох числових значень.

    Parameters:
        digit1 (int | float): Перше число.
        digit2 (int | float): Друге число (не може бути нулем).

    Returns:
        float: Частка digit1 поділено на digit2.

    Raises:
        ZeroDivisionError: Якщо digit2 дорівнює нулю.
    """
    if digit2 == 0:
        raise ZeroDivisionError("Ділення на нуль неможливе.")
    return digit1 / digit2


def calculator():
    """Простий консольний калькулятор."""
    print("Простий калькулятор")
    print("Доступні операції: +, -, *, /")
    print("Введіть 'exit' для виходу")

    while True:
        try:
            operation = input("Введіть операцію (+, -, *, /): ").strip()
            if operation.lower() == 'exit':
                print("До побачення!")
                break
            if operation not in ['+', '-', '*', '/']:
                print("Невірна операція. Спробуйте ще раз.")
                continue

            digit1 = float(input("Введіть перше число: "))
            digit2 = float(input("Введіть друге число: "))

            if operation == '+':
                result = sum_values(digit1, digit2)
            elif operation == '-':
                result = subtract_values(digit1, digit2)
            elif operation == '*':
                result = multiply_values(digit1, digit2)
            elif operation == '/':
                result = divide_values(digit1, digit2)

            print(f"Результат: {digit1} {operation} {digit2} = {result}")

        except ValueError:
            print("Невірне число. Спробуйте ще раз.")
        except ZeroDivisionError as e:
            print(f"Помилка: {e}")


if __name__ == "__main__":
    calculator()
