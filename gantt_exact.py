import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ───────────────────  chart data  ────────────────────
project_start = dt.date(2025, 6, 5)          # left-most date

tasks = [  # (label, offset-days, duration-days, colour)
    ("Requirements Finalization", 0,  2, "#FDB813"),  # orange-yellow
    ("UI/UX Design",              2,  5, "#F97306"),  # strong orange
    ("Backend Development",       3, 13, "#E50000"),  # crimson
    ("Frontend Development",      8, 13, "#FF33CC"),  # pink
    ("Integration",              21,  4, "#1E90FF"),  # bright blue
    ("Internal Testing",         25,  4, "#00CED1"),  # teal
    ("CI/CD Setup",              29,  4, "#00A550"),  # green
    ("Server Configuration",     29,  4, "#8DC63F"),  # light green
    ("Deployment to Prod",       33,  1, "#FF9E00"),  # amber
    ("Smoke Testing",            34,  1, "#FF6F00"),  # deep amber
    ("UAT Test Case Prep",       33,  1, "#FF0040"),  # red-pink
    ("UAT Execution",            35,  5, "#FF66CC"),  # light pink
    ("Bug Fix & Retest",         40,  3, "#33C1FF"),  # sky-blue
    ("Final Sign-off",           43,  1, "#05C3DD"),  # cyan
]

# ───────────────────  build the figure  ────────────────────
plt.rcParams["font.size"] = 12
fig, ax = plt.subplots(figsize=(14, 7.5))

for row, (label, offset, span, colour) in enumerate(tasks):
    start = project_start + dt.timedelta(days=offset)
    ax.barh(
        y=row,
        width=span,
        left=mdates.date2num(start),
        height=0.6,
        color=colour,
        edgecolor="none",
    )

# ─────────────  axis, grid & title styling  ───────────────
ax.set_yticks(range(len(tasks)))
ax.set_yticklabels([t[0] for t in tasks])

ax.invert_yaxis()                         # top-to-bottom order
ax.xaxis_date()
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
ax.set_xlabel("Date")
ax.set_title("Gantt Chart – Development, Deployment & UAT (1.5-month window)",
             pad=20, fontsize=16, weight="bold")

# match background / grid exactly like the uploaded image
ax.grid(axis="x", which="major", linestyle=":", color="#DDDDDD")
ax.grid(axis="y", visible=False)          # no horizontal grid
ax.set_axisbelow(True)                    # grid behind bars
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

fig.tight_layout()
fig.savefig("gantt_exact.png", dpi=300)   # identical output
plt.show()
