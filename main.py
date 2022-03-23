import csv
import plotly.graph_objects as go

from pulp import LpMaximize, LpProblem, LpStatus, lpSum, LpVariable

T = []  # время начала выполнения заявки
V = []  # объем топлива в заявках

with open('requests.csv', 'r', newline='') as CSVFile:
    reader = csv.DictReader(CSVFile, delimiter=';')
    for row in reader:
        T.append(int(row["time"]))
        V.append(int(row["volume"]))

countRequests = len(V)  # количество заявок
countBunkers = 2  # количество бункеровщиков для выполнения заявок
Vmax = 100  # максимальный объём бункеровщика
TFull = 30  # время заправки полного бака
deltaT = []  # время конца выполнения заявки

for i in range(0, countRequests):
    deltaT.append(T[i] + V[i])

for i in range(0, countRequests):
    print(f"Заявка {i + 1} (x{i})\nВремя начала: {T[i]}"
          f"\nВремя конца: {deltaT[i]}"
          f"\nОбьём заявки: {V[i]}\n")

model = LpProblem(name="maximizing_requests", sense=LpMaximize)

# Инициализация переменных решения: x - выполнение заявки бункеровщиком,
# y - пополнение топливного бака бункеровщика, CV - объем пополняемого топлива
x = {(b, i): LpVariable(name=f"Request{i:02}_{b} (x{i}_{b})", cat="Binary") for i in range(0, countRequests) for b in
     range(0, countBunkers)}
y = {(b, i): LpVariable(name=f"Refill{i:02}_{b} (y{i}_{b} )", cat="Binary") for i in range(0, countRequests) for b in
     range(0, countBunkers)}
CV = {(b, i): LpVariable(name=f"FillValue{i:02}_{b} ", lowBound=0, upBound=100, cat="Integer")
      for i in range(0, countRequests) for b in range(0, countBunkers)}

# Ограничение на количество выполняемых заявок
model += lpSum([x[b, i] for b in range(0, countBunkers) for i in range(0, countRequests)]) <= countRequests

# Ограничение на однозначное выполнение заявки бункеровщиком
for i in range(0, countRequests):
    model += lpSum([x[b, i] for b in range(0, countBunkers)]) <= 1

# Ограничения для каждого бункеровщика
for b in range(0, countBunkers):
    # Ограничения на объём бака
    for i in range(0, countRequests):
        a = 0
        for j in range(0, i + 1):
            a += (CV[b, j] - x[b, j] * V[j])
        model += (a <= 0, f"Заправлено после {i + 1} бункеровки(ок) для {b + 1} бункеровщика")
        model += (a >= -Vmax, f"Объем бака после {i + 1} заявки(ок) для {b + 1} бункеровщика")
        model += (CV[b, i] <= Vmax * y[b, i], f"Не достаточно топлива для {i + 1} заявки для {b + 1} бункеровщика")
    model += (y[b, countRequests - 1] == 0, f'Ограничение на заправку в конце очереди {b + 1} бункеровщика')

    # Ограничения на время поплнения
    for i in range(1, countRequests):
        model += ((T[i] - deltaT[i - 1]) * y[b, i - 1] - TFull * (x[b, i] - y[b, i]) >=
                  (T[i] - deltaT[i - 1] - TFull) * x[b, i] + TFull * (y[b, i] - 1),
                  f"Свободное время после {i + 1} заявки для {b + 1} бункеровщика")
        model += ((x[b, i]) * (T[i] - deltaT[i - 1]) >=
                  TFull * (y[b, i - 1] + x[b, i - 1] - 1), f"Остаток времени на {i + 1} для {b + 1} бункеровщика")

# Целевуая функция - сумма x (выполненных заявок)
model += lpSum(x.values())

# Решаем задачу оптимизации
status = model.solve()

print(f"status: {model.status}, {LpStatus[model.status]}")
print(f"objective: {model.objective.value()}\n")

# Вывод переменных
for var in model.variables():
    print(f"{var.name}: {var.value()}")

# Вывод ограничений
# for name, constraint in model.constraints.items():
#     print(f"{name}: {constraint.value()}")

# Визуализация данных
allT = []
for i in range(0, countRequests):
    allT.append(T[i])
    allT.append(deltaT[i])

fig = go.Figure()
for b in range(0, countBunkers):
    thisY = []
    for i in range(0, countRequests):
        if x[b, i].varValue == 1:
            thisY.append(b)
            thisY.append(b)
        else:
            thisY.append(None)
            thisY.append(None)

    fig.add_trace(go.Scatter(
        x=allT,
        y=thisY,
        name=f'Bunker {b + 1}',
        line=dict(width=40)

    ))
fig.update_layout(
    yaxis=dict(
        tickmode='array',
        tickvals=[b for b in range(0, countBunkers)],
        ticktext=[f'Bunker {b + 1}' for b in range(0, countBunkers)],
    ),
    xaxis=dict(
        tickmode='array',
        tickvals=allT
    )
)
for i in range(len(allT)):
    fig.add_vline(x=allT[i], line_width=2, line_dash="dot", line_color="SkyBlue")
fig.update_layout(legend_orientation="h")
fig.show()
