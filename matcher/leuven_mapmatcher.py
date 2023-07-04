import pandas as pd
from leuvenmapmatching.matcher.distance import DistanceMatcher
from leuvenmapmatching.map.inmem import InMemMap

from .base import Matcher
from utils import wgs2gcj


class LeuvenMatcher(Matcher):
    def __init__(self, name="leuven_matcher", graph=None, bgimg=None, extent=[]):
        assert graph != None, "You must supply a graph."
        super().__init__(name, graph, bgimg, extent)

    def init_matcher(self):
        self.map_con = InMemMap(self.name, use_latlon=True)
        for node in self.G.nodes:
            self.map_con.add_node(node, wgs2gcj(self.G.nodes[node]['y'], self.G.nodes[node]['x']))  # id, lat, lon
        for node_s, node_e in self.G.edges():
            self.map_con.add_edge(node_s, node_e)
            self.map_con.add_edge(node_e, node_s)
        
        # use lonlat false
        # self.matcher = DistanceMatcher(self.map_con, max_dist=50, obs_noise=2, min_prob_norm=0.04, max_lattice_width=5)
        # use lonlat true
        self.matcher = DistanceMatcher(self.map_con, max_dist=50000, obs_noise=100, min_prob_norm=0.01, obs_noise_ne=100, 
                                       dist_noise=500, max_lattice_width=5)  # Parameters work in Chengdu

    def match_traj(self, traj, visualize=False, save_time_tag=False, segment_projected=False):
        # traj: [(lon_1, lat_1), (lon_2, lat_2), ...] or [(lon_1, lat_1, t1), (lon_2, lat_2, t2), ...]
        assert len(traj) > 0

        if segment_projected:
            nodes, matched_routes = self._projected_match(traj)
        else:
            nodes = self._only_nodes_match(traj)
            matched_routes = [(node, self.G.nodes[node]['x'], self.G.nodes[node]['y']) for node in nodes]

        if visualize:
            self.visualize(traj, nodes, time_tag=save_time_tag)

        return matched_routes
        
    def _projected_match(self, traj):
        assert len(traj[0]) == 3, "Only 3D trajectory is supported when segment_projected is True"

        nodes = self._only_nodes_match(traj)

        trip = []
        for state in self.matcher.lattice_best:
            trip.append(['-'.join([str(state.edge_m.l1), str(state.edge_m.l2)]), state.obs, state.obs_ne])  # state.edge_m.l2 is int type
        trip = pd.DataFrame(trip, columns=['road', 'obs', 'obs_ne'])

        return nodes, trip

    def _only_nodes_match(self, traj):
        assert len(traj[0]) == 2 or len(traj[0]) == 3

        time_obtain = False
        if len(traj[0]) == 3:
            time_obtain = True
        
        if time_obtain:
            timestamps = [e[2] for e in traj]
            traj = [e[:2] for e in traj]

        states, _ = self.matcher.match(traj)
        nodes = self.matcher.path_pred_onlynodes  # traj consisted of nodes

        # with timestamps
        # if time_obtain:
        #     if len(self.matcher.lattice_best) == len(timestamps):
        #         lattice = list((*e.key, int(timestamp)) for e, timestamp in zip(self.matcher.lattice_best, timestamps))  # traj consisted of state transitiions
        #     else:
        #         lattice = []
        #         timestamps = iter(timestamps)
        #         timestamp = next(timestamps)
        #         for e in self.matcher.lattice_best:
        #             e = e.key
        #             lattice.append((*e, timestamp))
        #             if int(e[2]):
        #                 timestamp = next(timestamps)
        #     return self.get_node_timestamps(lattice)
        # else:
        #     return nodes

        return nodes

    @staticmethod
    def get_node_timestamps(traj):
        traj_node = []
        end_node = traj[0][0]
        for node_state in traj:
            start_node, timestamp = node_state[0], node_state[-1]
            if start_node == end_node:
                traj_node.append([start_node, timestamp])
                end_node = node_state[1]
        traj_node.append([end_node, timestamp])
        return traj_node
    