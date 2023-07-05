import os
import pickle
import warnings

import numpy as np
import pandas as pd

from matcher.leuven_mapmatcher import LeuvenMatcher
from utils import traj_iter

warnings.filterwarnings('ignore')


city = 'chengdu'
data_path = '/data/ZhouZeyu/RoadAndTraj/data/'
traj_path = os.path.join(data_path, 'traj/')
result_file_path = os.path.join(data_path, 'exports/')
result_file_name = os.path.join(result_file_path, 'chengdu_part%d_%02d')

g = pickle.load(open('data/chengdu_graph.pkl', 'rb'))
matcher = LeuvenMatcher(city, graph=g, bgimg='data/chengdu_bound.jpg', extent=[104.0421, 104.1291, 30.6528, 30.7265])
matcher.init_matcher()

num_part = 0
num_dump = 0
trips = []
trip_info = []
for trip, driver_id in traj_iter(traj_path, ['chengdushi_1001_1010.csv']):
    traj = [[e[1], e[0], e[2]] for e in trip]
    res_traj = matcher.match_traj(traj, visualize=False, save_time_tag=True, segment_projected=True)
    if res_traj is not None:
        res_traj = res_traj.reset_index().rename(columns={'index': 'seq_i'})
        res_traj['trip'] = num_dump
        trips.append(res_traj)

        trip_info.append([num_dump, res_traj['timestamp'].min(), res_traj['timestamp'].max(),
                          res_traj.loc[~res_traj['road'].duplicated(), 'length'].sum() / 1000, driver_id])

        num_dump += 1
        
    if num_dump % 10000 == 0:
        trips = pd.concat(trips)
        trip_info = pd.DataFrame(trip_info, columns=['trip', 'start', 'end', 'length', 'driver'])
        road_info = matcher.edge_info

        trips.to_hdf('exports/chengdu%02d_part%02d.h5' % (1, num_part), key='trips')
        trip_info.to_hdf('exports/chengdu%02d_part%02d.h5' % (1, num_part), key='trip_info')
        road_info.to_hdf('exports/chengdu%02d_part%02d.h5' % (1, num_part), key='road_info')

        num_part += 1
        trips = []
        trip_info = []

# trips.to_hdf('exports/small_chengdu.h5', key='trips')
# trip_info.to_hdf('exports/small_chengdu.h5', key='trip_info')
# road_info.to_hdf('exports/small_chengdu.h5', key='road_info')

trips.to_hdf('exports/chengdu%02d_part%02d.h5' % (1, num_part), key='trips')
trip_info.to_hdf('exports/chengdu%02d_part%02d.h5' % (1, num_part), key='trip_info')
road_info.to_hdf('exports/chengdu%02d_part%02d.h5' % (1, num_part), key='road_info')
