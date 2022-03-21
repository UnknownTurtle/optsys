from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable, LpAffineExpression

# Создаем модель
model = LpProblem(name="maximizing_requests", sense=LpMaximize)

# Количество топлива в заявках
V = [40, 10, 20, 50, 50, 20, 10, 20, 40, 20, 90]
# V = [40, 50, 20, 50, 50, 40]
# Количество заявок
count = len(V)
# Время начала заправки
T = [10, 100, 170, 210, 270, 330, 370, 400, 440, 490, 560]
# T = [10, 100, 170, 210, 270, 340]
# Время конца заправки
deltaT = [0] * count
for i in range(0, count):
    deltaT[i] = T[i] + V[i]

for i in range(0, count):
    print(f"Заявка {i + 1} (x{i})\nВремя начала: {T[i]}"
          f"\nВремя конца: {deltaT[i]}"
          f"\nОбьём заявки: {V[i]}\n")

# Максимальный объём бункеровщика
Vmax = 100
# Время заправки полного бака
TFull = 30

# Инициализируем переменные решения: x - выполнение заявки,
# y - пополнение топлива, CV - объем пополняемого топлива
x = {i: LpVariable(name=f"Request{i} (x{i})", cat="Binary") for i in range(0, count)}
y = {i: LpVariable(name=f"Refill{i} (y{i})", cat="Binary") for i in range(0, count)}
# x = {i: LpVariable(name=f"Request{i}", lowBound=0, upBound=1, cat="Integer") for i in range(0, count)}
# y = {i: LpVariable(name=f"Refill{i}", lowBound=0, upBound=1, cat="Integer") for i in range(0, count)}
CV = {i: LpVariable(name=f"FillValue{i}", lowBound=0, upBound=100, cat="Integer")
      for i in range(0, count)}

# Ограничения на объём бака
for i in range(0, count):
    a = 0
    for j in range(0, i + 1):
        a += (CV[j] - x[j] * V[j])
    model += (a <= 0, f"Заправлено после {i + 1} бункеровки(ок)")
    model += (a >= -Vmax, f"Объем бака после {i + 1} заявки(ок)")

for i in range(0, count):
    model += (CV[i] <= Vmax * y[i], f"Не достаточно топлива для {i} заявки")

# Ограничения на время поплнения
for i in range(1, count):
    model += ((T[i] - deltaT[i - 1]) * y[i - 1] - TFull * (x[i] - y[i]) >=
              (T[i] - deltaT[i - 1] - TFull) * x[i] + TFull * (y[i] - 1),
              f"Свободное время после {i} заявки")
    model += ((x[i]) * (T[i] - deltaT[i - 1]) >=
              TFull * (y[i - 1] + x[i-1] - 1), f"Остаток времени на {i} ")

# не нужно пополнять запасы в конце очереди
model += (y[count-1] == 0, 'Ограничение на последний y')

# ограничение на единовременное выполнение заявки или пополнение ресурсов
# for i in range(0, count):
#     model += (x[i] + y[i] == 1)

# Целевуая функция - сумма x - выполненных заявок
model += lpSum(x.values())

# Решаем задачу оптимизации
status = model.solve()

print(f"status: {model.status}, {LpStatus[model.status]}")
print(f"objective: {model.objective.value()}\n")

for var in model.variables():
    print(f"{var.name}: {var.value()}")
for name, constraint in model.constraints.items():
    print(f"{name}: {constraint.value()}")
