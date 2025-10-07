import random
import math
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ------------------------------
# 1) Seed and simulation count
# ------------------------------
random_seed = 12345
n_sims = 10000
random.seed(random_seed)

# ------------------------------
# 2) Core parameters (easy to edit)
# ------------------------------
years = 5
days_per_year = 365
total_days = years * days_per_year

# Financial parameters
annual_discount_rate = 0.05
energy_price_noise = 0.0
oven_hours_per_day = 8

# Investments
invest_current = 0.0
invest_A = 160000.0
invest_B = 240000.0
invest_C_support = 280000.0
invest_C_no_support = 330000.0
support_probability_C = 0.10

# Annual maintenance costs
maint_current = 15000.0
maint_A = 20000.0
maint_B = 25000.0
maint_C = 30000.0

# Daily failure probabilities (non-critical)
p_fail_current = 0.03
p_fail_A = 0.02
p_fail_B = 0.02
p_fail_C = 0.01

# Repair cost baseline and variability
repair_cost_base = 5000.0
repair_cost_sigma = 0.5

# Batch capacity per option (bumpers per batch)
capacity_current = 300
capacity_A = 180
capacity_B = 5200
capacity_C = 220

# Energy consumption per hour (units/hour)
oven_gas_current = 2.7
oven_gas_A = 2.2
oven_gas_B = 2.0
oven_gas_C = 1.7

oven_electric_current = 3.0
oven_electric_A = 2.7
oven_electric_B = 2.5
oven_electric_C = 1.9

# Energy prices (base values)
price_gas_base = 1.30
price_electric_base = 1.80

# Building base energy consumption per day
building_gas_base = 55.0
building_electric_base = 320.0

# Building energy savings (%) per option (expressed as decimals)
saving_gas_current = 0.00
saving_gas_A = 0.05
saving_gas_B = 0.10
saving_gas_C = 0.15

saving_electric_current = 0.03
saving_electric_A = 0.10
saving_electric_B = 0.15
saving_electric_C = 0.15

# Critical failure probabilities for current oven (one per year at most)
crit_probs = [0.02, 0.04, 0.06, 0.08, 0.10]
crit_failure_cost = 500000.0

# Batch size probabilities per year (lists align with years)
batch_sizes = [120, 160, 200, 240]
p_120 = [0.25, 0.30, 0.30, 0.35, 0.40]
p_160 = [0.25, 0.25, 0.30, 0.30, 0.30]
p_200 = [0.25, 0.25, 0.20, 0.20, 0.20]
p_240 = [0.25, 0.20, 0.20, 0.15, 0.10]

# ------------------------------
# Helper functions
# ------------------------------
def pick_batch_size(year_index):
    """Select daily batch size based on year-specific probabilities."""
    draw = random.random()
    threshold = p_120[year_index]
    if draw < threshold:
        return 120
    draw -= threshold
    threshold = p_160[year_index]
    if draw < threshold:
        return 160
    draw -= threshold
    threshold = p_200[year_index]
    if draw < threshold:
        return 200
    return 240

def discounted_value(cost_value, day_index):
    """Discount a daily cost back to present value."""
    exponent = day_index / days_per_year
    factor = math.pow(1.0 + annual_discount_rate, exponent)
    return cost_value / factor

def percentile_from_sorted(values, p):
    """Compute percentile using linear interpolation."""
    if not values:
        return 0.0
    if p <= 0:
        return values[0]
    if p >= 1:
        return values[-1]
    position = p * (len(values) - 1)
    lower_index = int(math.floor(position))
    upper_index = int(math.ceil(position))
    if lower_index == upper_index:
        return values[lower_index]
    weight = position - lower_index
    return values[lower_index] * (1.0 - weight) + values[upper_index] * weight

# ------------------------------
# Pre-computed daily constants per option (building energy after savings)
# ------------------------------
building_gas_current = building_gas_base * (1.0 - saving_gas_current)
building_gas_A = building_gas_base * (1.0 - saving_gas_A)
building_gas_B = building_gas_base * (1.0 - saving_gas_B)
building_gas_C = building_gas_base * (1.0 - saving_gas_C)

building_electric_current = building_electric_base * (1.0 - saving_electric_current)
building_electric_A = building_electric_base * (1.0 - saving_electric_A)
building_electric_B = building_electric_base * (1.0 - saving_electric_B)
building_electric_C = building_electric_base * (1.0 - saving_electric_C)

gas_units_current = building_gas_current + oven_hours_per_day * oven_gas_current
gas_units_A = building_gas_A + oven_hours_per_day * oven_gas_A
gas_units_B = building_gas_B + oven_hours_per_day * oven_gas_B
gas_units_C = building_gas_C + oven_hours_per_day * oven_gas_C

electric_units_current = building_electric_current + oven_hours_per_day * oven_electric_current
electric_units_A = building_electric_A + oven_hours_per_day * oven_electric_A
electric_units_B = building_electric_B + oven_hours_per_day * oven_electric_B
electric_units_C = building_electric_C + oven_hours_per_day * oven_electric_C

# Daily maintenance costs (spread evenly across the year)
maint_daily_current = maint_current / days_per_year
maint_daily_A = maint_A / days_per_year
maint_daily_B = maint_B / days_per_year
maint_daily_C = maint_C / days_per_year

# Containers for simulation results
pv_costs_current = []
pv_costs_A = []
pv_costs_B = []
pv_costs_C = []

# ------------------------------
# 4) Simulation loops
# ------------------------------
for sim in range(n_sims):
    # Determine initial present value with upfront investment costs
    npv_current_sim = invest_current
    npv_A_sim = invest_A
    npv_B_sim = invest_B
    if random.random() < support_probability_C:
        invest_C = invest_C_support
    else:
        invest_C = invest_C_no_support
    npv_C_sim = invest_C

    # Prepare critical failure days for current oven (one draw per year)
    critical_days = [-1, -1, -1, -1, -1]
    for year in range(years):
        if random.random() < crit_probs[year]:
            random_day_in_year = random.randint(0, days_per_year - 1)
            critical_days[year] = year * days_per_year + random_day_in_year

    # Loop through each day of the analysis period
    for day in range(total_days):
        year_index = day // days_per_year
        batch = pick_batch_size(year_index)

        # Daily energy prices with shared random noise across all options
        gas_price_today = price_gas_base * (1.0 + random.uniform(-energy_price_noise, energy_price_noise))
        electric_price_today = price_electric_base * (1.0 + random.uniform(-energy_price_noise, energy_price_noise))

        # ------------------
        # Current oven
        # ------------------
        overage_cost_current = 0.0
        repair_cost_current = 0.0
        production_current = batch
        failure_today_current = False

        # Check regular failure
        if random.random() < p_fail_current:
            production_current = 0
            failure_today_current = True
            repair_factor = 1.0 + random.gauss(0.0, repair_cost_sigma)
            if repair_factor < 0.0:
                repair_factor = 0.0
            repair_cost_current = repair_cost_base * repair_factor

        # Check critical failure for the year (only if not already failed today)
        if critical_days[year_index] == day:
            production_current = 0
            failure_today_current = True
            repair_cost_current += crit_failure_cost

        # Apply capacity and overage only if production occurs
        if not failure_today_current:
            if batch > capacity_current:
                overage_current = batch - capacity_current
                production_current = capacity_current
                overage_cost_current = overage_current * 2.0
            else:
                production_current = batch
                overage_cost_current = 0.0
        else:
            overage_cost_current = 0.0

        # Energy consumption and cost
        energy_cost_current = gas_units_current * gas_price_today + electric_units_current * electric_price_today
        total_cost_current = energy_cost_current + maint_daily_current + repair_cost_current + overage_cost_current
        npv_current_sim += discounted_value(total_cost_current, day + 1)

        # ------------------
        # Oven A
        # ------------------
        overage_cost_A = 0.0
        repair_cost_A = 0.0
        production_A = batch
        failure_today_A = False

        if random.random() < p_fail_A:
            production_A = 0
            failure_today_A = True
            repair_factor = 1.0 + random.gauss(0.0, repair_cost_sigma)
            if repair_factor < 0.0:
                repair_factor = 0.0
            repair_cost_A = repair_cost_base * repair_factor

        if not failure_today_A:
            if batch > capacity_A:
                overage_A = batch - capacity_A
                production_A = capacity_A
                overage_cost_A = overage_A * 2.0
            else:
                production_A = batch
                overage_cost_A = 0.0
        else:
            overage_cost_A = 0.0

        energy_cost_A = gas_units_A * gas_price_today + electric_units_A * electric_price_today
        total_cost_A = energy_cost_A + maint_daily_A + repair_cost_A + overage_cost_A
        npv_A_sim += discounted_value(total_cost_A, day + 1)

        # ------------------
        # Oven B
        # ------------------
        overage_cost_B = 0.0
        repair_cost_B = 0.0
        production_B = batch
        failure_today_B = False

        if random.random() < p_fail_B:
            production_B = 0
            failure_today_B = True
            repair_factor = 1.0 + random.gauss(0.0, repair_cost_sigma)
            if repair_factor < 0.0:
                repair_factor = 0.0
            repair_cost_B = repair_cost_base * repair_factor

        if not failure_today_B:
            if batch > capacity_B:
                overage_B = batch - capacity_B
                production_B = capacity_B
                overage_cost_B = overage_B * 2.0
            else:
                production_B = batch
                overage_cost_B = 0.0
        else:
            overage_cost_B = 0.0

        energy_cost_B = gas_units_B * gas_price_today + electric_units_B * electric_price_today
        total_cost_B = energy_cost_B + maint_daily_B + repair_cost_B + overage_cost_B
        npv_B_sim += discounted_value(total_cost_B, day + 1)

        # ------------------
        # Oven C
        # ------------------
        overage_cost_C = 0.0
        repair_cost_C = 0.0
        production_C = batch
        failure_today_C = False

        if random.random() < p_fail_C:
            production_C = 0
            failure_today_C = True
            repair_factor = 1.0 + random.gauss(0.0, repair_cost_sigma)
            if repair_factor < 0.0:
                repair_factor = 0.0
            repair_cost_C = repair_cost_base * repair_factor

        if not failure_today_C:
            if batch > capacity_C:
                overage_C = batch - capacity_C
                production_C = capacity_C
                overage_cost_C = overage_C * 2.0
            else:
                production_C = batch
                overage_cost_C = 0.0
        else:
            overage_cost_C = 0.0

        energy_cost_C = gas_units_C * gas_price_today + electric_units_C * electric_price_today
        total_cost_C = energy_cost_C + maint_daily_C + repair_cost_C + overage_cost_C
        npv_C_sim += discounted_value(total_cost_C, day + 1)

    # Store simulation results
    pv_costs_current.append(npv_current_sim)
    pv_costs_A.append(npv_A_sim)
    pv_costs_B.append(npv_B_sim)
    pv_costs_C.append(npv_C_sim)

# ------------------------------
# 5) Post-processing statistics
# ------------------------------
pv_costs_current_sorted = sorted(pv_costs_current)
pv_costs_A_sorted = sorted(pv_costs_A)
pv_costs_B_sorted = sorted(pv_costs_B)
pv_costs_C_sorted = sorted(pv_costs_C)

median_current = percentile_from_sorted(pv_costs_current_sorted, 0.5)
median_A = percentile_from_sorted(pv_costs_A_sorted, 0.5)
median_B = percentile_from_sorted(pv_costs_B_sorted, 0.5)
median_C = percentile_from_sorted(pv_costs_C_sorted, 0.5)

mean_current = sum(pv_costs_current) / len(pv_costs_current)
mean_A = sum(pv_costs_A) / len(pv_costs_A)
mean_B = sum(pv_costs_B) / len(pv_costs_B)
mean_C = sum(pv_costs_C) / len(pv_costs_C)

p5_current = percentile_from_sorted(pv_costs_current_sorted, 0.05)
p5_A = percentile_from_sorted(pv_costs_A_sorted, 0.05)
p5_B = percentile_from_sorted(pv_costs_B_sorted, 0.05)
p5_C = percentile_from_sorted(pv_costs_C_sorted, 0.05)

p95_current = percentile_from_sorted(pv_costs_current_sorted, 0.95)
p95_A = percentile_from_sorted(pv_costs_A_sorted, 0.95)
p95_B = percentile_from_sorted(pv_costs_B_sorted, 0.95)
p95_C = percentile_from_sorted(pv_costs_C_sorted, 0.95)

# Probability of being the best
best_counts = [0.0, 0.0, 0.0, 0.0]
for index in range(n_sims):
    values = [pv_costs_current[index], pv_costs_A[index], pv_costs_B[index], pv_costs_C[index]]
    best_value = min(values)
    winners = 0
    if abs(values[0] - best_value) < 1e-9:
        winners += 1
    if abs(values[1] - best_value) < 1e-9:
        winners += 1
    if abs(values[2] - best_value) < 1e-9:
        winners += 1
    if abs(values[3] - best_value) < 1e-9:
        winners += 1
    share = 1.0 / winners
    if abs(values[0] - best_value) < 1e-9:
        best_counts[0] += share
    if abs(values[1] - best_value) < 1e-9:
        best_counts[1] += share
    if abs(values[2] - best_value) < 1e-9:
        best_counts[2] += share
    if abs(values[3] - best_value) < 1e-9:
        best_counts[3] += share

prob_best_current = best_counts[0] / n_sims
prob_best_A = best_counts[1] / n_sims
prob_best_B = best_counts[2] / n_sims
prob_best_C = best_counts[3] / n_sims

# ------------------------------
# 6) Output results
# ------------------------------
print("Seed:", random_seed)
print("Energy price noise:", energy_price_noise)
print()
print("Option\tMean PV Cost\tMedian PV Cost\tP5\tP95\tProb. Lowest Cost")
print("Current\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.4f}".format(mean_current, median_current, p5_current, p95_current, prob_best_current))
print("A\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.4f}".format(mean_A, median_A, p5_A, p95_A, prob_best_A))
print("B\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.4f}".format(mean_B, median_B, p5_B, p95_B, prob_best_B))
print("C\t{:.2f}\t{:.2f}\t{:.2f}\t{:.2f}\t{:.4f}".format(mean_C, median_C, p5_C, p95_C, prob_best_C))

# Histograms
plt.figure(figsize=(10, 8))
plt.subplot(2, 2, 1)
plt.hist(pv_costs_current, bins=30)
plt.title("Current")

plt.subplot(2, 2, 2)
plt.hist(pv_costs_A, bins=30)
plt.title("Oven A")

plt.subplot(2, 2, 3)
plt.hist(pv_costs_B, bins=30)
plt.title("Oven B")

plt.subplot(2, 2, 4)
plt.hist(pv_costs_C, bins=30)
plt.title("Oven C")

plt.tight_layout()
plt.savefig("npv_histograms.png")
