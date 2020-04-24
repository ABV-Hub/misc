import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
import sys
import math
from datetime import date, timedelta

def make_df_from_csv(fname):
    """Make df"""
    df = pd.read_csv(fname)
    df.index = pd.to_datetime(df['DateTime'])
    df.drop(columns=['DateTime'], inplace=True)
    df['total_time'] = df.index.hour * 60 + df.index.minute + df.index.second / 60
    df['avg_speed'] = df.Distance / df.total_time * 60
    pb_dist = df['Distance'].max()
    pb_speed = df['avg_speed'].max()
    last_dist = df['Distance'][-1]
    last_speed = df['avg_speed'][-1]
    weeks = (df.index.date[-1] - df.index.date[0]).days // 7
    avg_speed = df['avg_speed'].mean()
    df['Speed_rolling_mean'] = df['avg_speed'].rolling(5).mean()
    avg_distance = df['Distance'].mean()
    df['Distance_rolling_mean'] = df['Distance'].rolling(5).mean()
    df['Runtime_rolling_mean'] = df['total_time'].rolling(5).mean()

    title1 = r"$\bf{Overall\ stats:}$"
    title2 = r"$\bf{Last\ run:}$"
    textstr = f'''
    {title1}
    ---------------------
    run_count: {df.shape[0]}
    run_freq: {df.shape[0] / weeks:.1f} runs/week
    mean_dist: {df.describe().loc['mean', 'Distance']:.2f} km
    mean_speed: {df.describe().loc['mean', 'avg_speed']:.2f} km/hr
    PB distance: {df.describe().loc['max', 'Distance']} km
    PB speed: {df.describe().loc['max', 'avg_speed']:.2f} km/hr

    {title2}
    ---------------
    distance: {last_dist}km
    speed: {last_speed:.2f}km/hr
    '''

    if pb_dist == last_dist:
        print(f'New PB distance! {pb_dist:.2f}km')
    if pb_speed == last_speed:
        print(f'New PB speed! {pb_speed:.2f}km/hr')

    return df, textstr, avg_speed, avg_distance


def check_progress_rate(df):
    """Warn if distance delta between last run and previous week max is > 10%"""
    last_run_dist = df['Distance'][-1]
    last_run_date = df.index[-1]
    tdelta_day = timedelta(days=1)
    tdelta_week = timedelta(days=1, weeks=1)
    nruns = df[last_run_date - tdelta_week:last_run_date - tdelta_day]['Distance'].shape[0]
    last_week_max = df[last_run_date - tdelta_week:last_run_date - tdelta_day]['Distance'].max()
    last_week_avg_dist = df[last_run_date - tdelta_week:last_run_date - tdelta_day]['Distance'].sum() / nruns
    if last_run_dist > last_week_avg_dist + last_week_avg_dist * 0.1:
        print(f'The last run exceeded the previous week average by {(last_run_dist - last_week_avg_dist) * 100 / last_week_avg_dist:.0f}%.')
    if last_run_dist > last_week_max + last_week_max * 0.1:
        print(f'The last run exceeded the previous week max by {(last_run_dist - last_week_max) * 100 / last_week_max:.0f}%.')
    return


def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)


def make_plot(df, textstr, avg_speed, avg_distance):
    """Make run plot"""
    fig, host = plt.subplots(figsize=(20,10), nrows=1, ncols=1)
    # create a second plot that is offset and only shows one spine
    fig.subplots_adjust(right=0.75)
    par1 = host.twinx()
    par2 = host.twinx()
    par2.spines["right"].set_position(("axes", 1.04))
    make_patch_spines_invisible(par2)
    par2.spines["right"].set_visible(True)

    # plot the data
    d1, = host.plot(df.avg_speed, "o-", label="Avg speed [km/h]", c='r')
    d2, = par1.plot(df.Distance, "o-", label="Distance [km]", c='g')
    d3 = par2.bar(df.index, height=df.total_time, label='Run time [min]', width=1.5, alpha=0.2, color='b')

    # add averages
    d4 = host.axhline(y=avg_speed, xmin=0, xmax=1, ls='-', lw=1.5, alpha=0.3, c='r', label='Avg speed abs')
    d5 = par1.axhline(y=avg_distance, xmin=0, xmax=1, ls='-', lw=1.5, alpha=0.3, c='g', label='Avg dist abs')

    # add rolling means
    d6, = host.plot(df.Speed_rolling_mean, ls='dashed', lw=1.5, c='r', label='Speed roll_mean_5')
    d7, = par1.plot(df.Distance_rolling_mean, ls='dashed', lw=1.5, c='g', label='Dist roll_mean_5')
    d8, = par2.plot(df.Runtime_rolling_mean, ls='dashed', lw=1.5, c='b', label='Time roll_mean_5')

    # add PB's
    pb_speed = (df.loc[df['avg_speed'] == df['avg_speed'].max()].index[0], df.loc[df['avg_speed'] == df['avg_speed'].max()]['avg_speed'][0])
    pb_distance = (df.loc[df['Distance'] == df['Distance'].max()].index[0], df.loc[df['Distance'] == df['Distance'].max()]['Distance'][0])
    host.plot(pb_speed[0], pb_speed[1], marker='*', c='r', markersize=15)
    par1.plot(pb_distance[0], pb_distance[1], marker='*', c='g', markersize=15)

    # dress up the plot
    start_date = df.index[0].date()
    host.set_title(f"Rob's run log from {start_date} to {date.today()}", fontsize=14)
    host.grid()
    host.set_xticks(ticks=df.index)
    host.set_xticklabels(df.index.date, rotation=90, fontsize=10)

    # set ylims
    min_speed = 2
    min_dist = 2
    min_time = 20
    max_speed = df['avg_speed'].max()
    max_dist = df['Distance'].max()
    max_yscale = max_speed if max_speed > max_dist else max_dist

    host.set_ylim(min_speed,int(math.ceil(max_yscale)))
    par1.set_ylim(min_dist,int(math.ceil(max_yscale)))
    max_time = df['total_time'].max()
    par2.set_ylim(min_time, int(math.ceil(max_time / 5.)) * 5)

    # add labels
    host.set_xlabel("Date", fontsize=12, c='k')
    host.set_ylabel("avg speed [km/h]", fontsize=12, c='r')
    par1.set_ylabel("Distance [km]", fontsize=12, c='g')
    par2.set_ylabel("Run time [min]", fontsize=12, c='b')

    # manage ticks
    tkw = {'size':4, 'width':1.5}

    #plt.xticks(np.arange(min(x), max(x)+1, 1.0))
    host.tick_params(axis='y', colors=d1.get_color(), **tkw)
    host.set_yticks(np.arange(math.floor(min_speed), math.ceil(max_speed) + 1, 1.0))
    par1.tick_params(axis='y', colors=d2.get_color(), **tkw)
    par1.set_yticks(np.arange(math.floor(min_dist), math.ceil(max_dist) + 1, 1.0))
    par2.tick_params(axis='y', colors='b', **tkw)
    par2.set_yticks(np.arange(math.floor(min_time), math.ceil(max_time) + 5, 5))
    host.tick_params(axis='x', **tkw)

    # add a legend
    data = [d1, d4, d6, d2, d5, d7, d3, d8]
    host.legend(data, [d.get_label() for d in data], loc=2, fontsize=12, bbox_to_anchor=(1.1, 0, 1., 1.))
    plt.legend

    # add stats
    props = dict(boxstyle='round', facecolor='white', alpha=0.7)
    host.text(1.11, 0.45, textstr, transform=host.transAxes, fontsize=10,
        verticalalignment='top', bbox=props)

    fig.tight_layout(pad=5)
    plt.show()
    return


if __name__ == "__main__":
    df, textstr, avg_speed, avg_distance = make_df_from_csv(sys.argv[1])
    check_progress_rate(df)
    make_plot(df, textstr, avg_speed, avg_distance)
