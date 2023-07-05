import os
import pickle

from matcher.leuven_mapmatcher import LeuvenMatcher
from utils import traj_iter


city = 'chengdu'
g = pickle.load(open('data/chengdu_graph.pkl', 'rb'))

matcher = LeuvenMatcher(city, graph=g, bgimg='data/chengdu_bound.jpg', extent=[104.0421, 104.1291, 30.6528, 30.7265])
matcher.init_matcher()
for i, (trip, _) in enumerate(traj_iter('data/', filenames=['small_chengdu.csv'])):
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
