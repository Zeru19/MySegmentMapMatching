import os
import pickle

import numpy as np

from matcher.leuven_mapmatcher import LeuvenMatcher


def traj_iter(data_dir='../data/'):
    """
    Trajectory data iterator
    """
    traj_path = data_dir
    for i, file in enumerate(['small_chengdu.csv']):
        with open(traj_path + file) as fp:
            line = fp.readline()
            while line:
                cols = line.split(',')
                user_id = cols[0]
                driver_id = cols[1]
                traj = cols[2:]
                traj[0] = traj[0][2:]
                traj[-1] = traj[-1][:-3]
                traj = traj[1::2] + traj[-1:]

                traj_array = np.array([list(p.strip().split(' ')) for p in traj]).astype(float)
                # timestamps = [traj_array[j, -1] for j in range(traj_array.shape[0])]
                # path = [tuple(traj_array[j, :2]) for j in range(traj_array.shape[0])]
                path = [tuple(traj_array[j, :]) for j in range(traj_array.shape[0])]
                line = fp.readline()
                yield path


city = 'chengdu'
g = pickle.load(open('data/chengdu_graph.pkl', 'rb'))

matcher = LeuvenMatcher(city, graph=g, bgimg='data/chengdu_bound.jpg', extent=[104.0421, 104.1291, 30.6528, 30.7265])
matcher.init_matcher()
for i, trip in enumerate(traj_iter('data/')):
    if i < 13:
        continue
    traj = [[e[1], e[0], e[2]] for e in trip]
    # traj = [[30.65307, 104.05592, 1541374541.0], [30.66739, 104.05219, 1541374840.0]]
    for i, e in enumerate(traj):
        if i % 5 == 0:
            print(e, ',')
    res_traj = matcher.match_traj(traj, visualize=True, save_time_tag=True, segment_projected=True)
    print(res_traj)
    break
