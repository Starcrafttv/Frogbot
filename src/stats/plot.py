from datetime import datetime, timedelta

from emoji import demojize
from matplotlib import pyplot as plt

plt.rcParams['axes.labelcolor'] = '#ffffff'
plt.rcParams['xtick.color'] = '#ffffff'
plt.rcParams['ytick.color'] = '#ffffff'
plt.rcParams['text.color'] = '#ffffff'
plt.rcParams['axes.edgecolor'] = '#ffffff'


# TODO alternative for smart_bounds function


async def get_stats(stats: list) -> bool:
    try:
        days = []
        active = []
        afk = []
        # Calculate the stats for each day
        for day in reversed(stats[1:]):
            y, m, d = day[0].split('-')
            days.append(f'{d}.{m}.{y[2:]}')
            active.append(day[1] / 3600)
            afk.append(day[2] / 3600)
        n = (len(days) + 10) // 10
        x = [i for i in range(len(days))]
        # Setup a new graph
        plt.clf()
        fig, ax = plt.subplots(1, 1)
        fig.patch.set_facecolor('#36393f')
        ax.set_facecolor('#36393f')
        ax.spines['top'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.spines['left'].set_color('none')
        # Create active and afk bars side by side
        ax.bar([i - 0.2 for i in x], active, width=0.4, alpha=0.8,
               align='center', color='#7289DA', zorder=3, label='Active')
        ax.bar([i + 0.2 for i in x], afk, width=0.4, alpha=0.8,
               align='center', color='orange', zorder=3, label='Afk')
        plt.grid(color='#2C2F33', linestyle=':', linewidth=1, axis='y', zorder=1)
        # ax.spines['left'].set_smart_bounds(True)
        # ax.spines['bottom'].set_smart_bounds(True)
        # Set the x-axis to the dates and not show all to avoid overlaying
        plt.xticks(x, days, rotation=40, ha='right')
        [l.set_visible(False) for (i, l) in enumerate(reversed(ax.xaxis.get_ticklabels())) if i % n != 0]
        ax.tick_params(axis='x', which='major', labelsize=12)
        ax.tick_params(axis='y', which='major', labelsize=12)
        ax.set_ylabel('Time in hours', fontsize=12)
        ax.set_xlabel('')
        ax.legend(frameon=False)
        plt.title(demojize(stats[0][1]), fontsize=15)
        plt.tight_layout()
        # Save the plot in a png
        plt.savefig('data/temp/stats.png', dpi=300, facecolor=fig.get_facecolor())
        return True
    except Exception as e:
        # If something goes wrong exit with False
        print(e)
        return False


async def get_raw_stats(username: str, timezone: int, last_days, active: list, afk: list) -> bool:
    try:
        dates = []
        xticks = []
        # Create normalized dates for the x-axis
        for i in range(last_days - 1, -1, -1):
            dates.append(str((datetime.utcnow() + timedelta(days=-i, hours=timezone)).date()))
            y, m, d = dates[-1].split('-')
            xticks.append(f'{d}.{m}.{y[2:]}')
        # Setup a new graph
        plt.clf()
        fig, ax = plt.subplots()
        fig.patch.set_facecolor('#36393f')
        fig.set_size_inches(8, 5)
        ax.set_facecolor('#36393f')
        ax.spines['top'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.spines['left'].set_color('none')
        x = [i for i in range(last_days)]

        ax = await add_plot_points(ax, active, dates, '#7289DA', 4)
        ax = await add_plot_points(ax, afk, dates, '#b9bbbe')

        plt.grid(color='#2C2F33', linestyle=':', linewidth=1, axis='both', zorder=1)
        plt.xticks(x, xticks, rotation=40, ha='right')
        n = (len(dates) + 10) // 10
        [l.set_visible(False) for (i, l) in enumerate(reversed(ax.xaxis.get_ticklabels())) if i %
         n != 0]
        ax.tick_params(axis='x', which='major', labelsize=12)
        ax.tick_params(axis='y', which='major', labelsize=12)
        ax.set_ylabel('')
        ax.set_xlabel('')
        # Set the y-axis ticks as hours
        plt.yticks([0, 3, 6, 9, 12, 15, 18, 21, 24], ['', '3:00', '6:00',
                                                      '9:00', '12:00', '15:00', '18:00', '21:00', '24:00'])
        plt.title(demojize(username), fontsize=15)
        plt.tight_layout()
        plt.savefig('data/temp/stats.png', dpi=500, facecolor=fig.get_facecolor())
        return True
    except Exception:
        return False


async def add_plot_points(ax, entries, dates, facecolor, zorder=3):
    for entry in entries:
        time = datetime.utcfromtimestamp(entry[0])
        for i in range(len(dates)):
            if entry[1] > 60 and str(time.date()) == dates[i]:
                ax.bar(
                    i,
                    entry[1] / 3600,
                    bottom=time.hour + (time.minute / 60) + (time.second / 3600),
                    width=0.5,
                    facecolor=facecolor,
                    zorder=zorder)
    return ax


async def get_leaderboard(usernames: str, total_stats: list, top: int, time_type: bool, description: str) -> bool:
    try:
        # Setup a new graph
        plt.clf()
        fig, ax = plt.subplots(1, 1)
        fig.patch.set_facecolor('#36393f')
        ax.set_facecolor('#36393f')
        ax.spines['top'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.spines['left'].set_color('none')
        # Set the leaderboard names on the y-axis
        plt.hlines(y=[demojize(name) for name in usernames], xmin=0, xmax=total_stats,
                   color='#7289DA', alpha=0.6, linewidth=70 / top, zorder=3)
        plt.plot(total_stats, [demojize(name) for name in usernames], 'o',
                 markersize=70 / top, color='#7289DA', alpha=1, zorder=3)
        plt.grid(color='#2C2F33', linestyle=':', linewidth=1, axis='x', zorder=1)
        # ax.spines['left'].set_smart_bounds(True)
        # ax.spines['bottom'].set_smart_bounds(True)
        ax.spines['bottom'].set_position(('axes', -0.03))
        ax.tick_params(axis='x', which='major', labelsize=12)
        ax.tick_params(axis='y', which='major', labelsize=70 / top)
        ax.set_xlabel('Time in days' if time_type else 'Total messages', fontsize=12)
        ax.set_ylabel('')
        plt.title(description, fontsize=15)
        plt.tight_layout()
        plt.savefig('data/temp/stats.png', dpi=300, facecolor=fig.get_facecolor())
        return True
    except Exception:
        return False


async def get_compare(users: list, user_stats, days, r_type: int) -> bool:
    try:
        plt.clf()
        width = 0.4
        x = [i for i in range(len(days))]
        if len(users) == 2:
            width = 0.4
            pos = [-width / 2, width / 2]
        elif len(users) == 3:
            width = 0.27
            pos = [-width, 0, width]
        elif len(users) == 4:
            width = 0.2
            pos = [-width * 1.5, -width / 2, width / 2, width * 1.5]
        else:
            return False
        n = (len(days) + 10) // 10
        ax = plt.subplot(1, 1, 1)
        colors = ['dodgerblue', 'yellow', 'firebrick', 'limegreen']
        fig, ax = plt.subplots(1, 1)
        fig.patch.set_facecolor('#36393f')
        ax.set_facecolor('#36393f')
        for i, user in enumerate(users):
            ax.bar([j + pos[i] for j in x], user_stats[i], width=width,
                   align='center', color=colors[i], zorder=3, label=demojize(user))
        plt.grid(color='#2C2F33', linestyle=':', linewidth=1, axis='y', zorder=1)
        # ax.spines['left'].set_smart_bounds(True)
        # ax.spines['bottom'].set_smart_bounds(True)
        ax.spines['top'].set_color('none')
        ax.spines['right'].set_color('none')
        ax.spines['left'].set_color('none')
        plt.xticks(x, days, rotation=40, ha='right')
        [l.set_visible(False) for (i, l) in enumerate(reversed(ax.xaxis.get_ticklabels())) if i % n != 0]
        ax.tick_params(axis='x', which='major', labelsize=12)
        ax.tick_params(axis='y', which='major', labelsize=12)
        if r_type == 1:
            ax.set_ylabel('Active time in hours', fontsize=12)
        elif r_type == 2:
            ax.set_ylabel('Afk time in hours', fontsize=12)
        elif r_type == 3:
            ax.set_ylabel('Messages', fontsize=12)
        ax.set_xlabel('')
        ax.legend(frameon=False)
        plt.tight_layout()
        plt.savefig('data/temp/stats.png', dpi=300, facecolor=fig.get_facecolor())
        return True
    except Exception:
        return False
