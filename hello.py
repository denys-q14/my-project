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
    """Простий консольний калькулятор з меню."""
    print("Простий калькулятор")
    print("Оберіть операцію:")

    while True:
        print("\nМеню:")
        print("1. Додавання (+)")
        print("2. Віднімання (-)")
        print("3. Множення (*)")
        print("4. Ділення (/)")
        print("5. Вихід")

        try:
            choice = input("Введіть номер операції (1-5): ").strip()
            if choice == '5':
                print("До побачення!")
                break
            if choice not in ['1', '2', '3', '4']:
                print("Невірний вибір. Спробуйте ще раз.")
                continue

            digit1 = float(input("Введіть перше число: "))
            digit2 = float(input("Введіть друге число: "))

            if choice == '1':
                operation = '+'
                result = sum_values(digit1, digit2)
            elif choice == '2':
                operation = '-'
                result = subtract_values(digit1, digit2)
            elif choice == '3':
                operation = '*'
                result = multiply_values(digit1, digit2)
            elif choice == '4':
                operation = '/'
                result = divide_values(digit1, digit2)

            print(f"Результат: {digit1} {operation} {digit2} = {result}")

        except ValueError:
            print("Невірне число. Спробуйте ще раз.")
        except ZeroDivisionError as e:
            print(f"Помилка: {e}")


if __name__ == "__main__":
    calculator()
