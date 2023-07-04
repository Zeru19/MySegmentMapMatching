import os
import datetime
import abc

import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import pandas as pd

from utils import gcj2wgs


class Matcher:
    def __init__(self, name, graph, bgimg=None, extent=[]):
        """ Base Matcher

        Args:
        --------
            name: a str object
            graph: a network Graph object
            bgimg: background image path
            extent: [min_lon, max_lon, min_lat, max_lat]
        """
        super().__init__()

        self.name = f"{name}-mapmatcher"
        self._load_graph(graph)
        self.bgimg = bgimg
        self.extent = extent

        self.matcher = None

    def __call__(self, *args, **kwds):
        return self.match_traj(*args, **kwds)
    
    def _load_graph(self, graph):
        self.G = graph

        node_info = []
        for node, info in self.G.nodes.items():
            # street_count: Count how many physical street segments connect to each node in a graph.
            node_info.append([node, info['y'], info['x'], info['street_count']])
        node_info = pd.DataFrame(node_info, columns=['osm_id', 'latitude', 'longitude', 'street_count'])
        node_info['node'] = list(range(len(node_info)))
        self.node_info = node_info

        self.node_id_map = {}
        for osm_id, node_id in zip(self.node_info['osm_id'], self.node_info['node']):
            self.node_id_map[osm_id] = node_id

        edge_info = []
        existed_edges = []
        for edge, info in self.G.edges.items():
            edge_name = '-'.join([str(edge[0]), str(edge[1])])
            if edge_name not in existed_edges:
                edge_info.append([
                    edge_name,
                    edge[0],
                    edge[1],
                    info['length'],
                    info.get('highway', 'unclassified')
                ])
                existed_edges.append(edge_name)
            
            edge_name = '-'.join([str(edge[1]), str(edge[0])])
            # if not info['oneway'] and edge_name not in existed_edges:
            if edge_name not in existed_edges:  # regard as undirected graph
                edge_info.append([
                    edge_name,
                    edge[1],
                    edge[0],
                    info['length'],
                    info.get('highway', 'unclassified')
                ])
                existed_edges.append(edge_name)
        edge_info = pd.DataFrame(edge_info, columns=['edge_name', 'o', 'd', 'length', 'highway'])
        edge_info['edge'] = list(range(len(edge_info)))
        edge_info = pd.merge(edge_info, self.node_info, left_on='o', right_on='osm_id', how='left')
        edge_info = pd.merge(edge_info, self.node_info, left_on='d', right_on='osm_id', how='left', suffixes=('_o', '_d'))
        edge_info['longitude'] = (edge_info['longitude_o'] + edge_info['longitude_d']) / 2
        edge_info['latitude'] = (edge_info['latitude_o'] + edge_info['latitude_d']) / 2
        self.edge_info = edge_info[['edge', 'edge_name', 'o', 'd', 'length', 'highway', 'longitude', 'latitude', 'o', 'longitude_o', 'latitude_o']]

        self.edge_id_map = {}
        for edge_name, edge_id in zip(self.edge_info['edge_name'], self.edge_info['edge']):
            self.edge_id_map[edge_name] = edge_id

    @abc.abstractmethod
    def init_matcher(self):
        pass

    def match_traj(self, traj, visualize=False, time_tag=False):
        if self.matcher is None:
            raise ValueError("matcher not initialized")
        matched_path = self.matcher.match(traj)
        if visualize:
            self.visualize(traj, matched_path, time_tag=time_tag)
        pass

    def visualize(self, traj, matched_path, time_tag=False):
        fig = plt.figure(figsize=(10, 10))

        if self.bgimg and len(self.extent) == 4:
            img = plt.imread(self.bgimg)
            ax = fig.add_subplot(projection=ccrs.PlateCarree())
            ax.use_sticky_edges = False
            ax.imshow(img, origin='upper', extent=self.extent, transform=ccrs.PlateCarree())
            ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
            ax.set_xlim([self.extent[0], self.extent[1]])
            ax.set_ylim([self.extent[2], self.extent[3]])
            
        else:
            ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
            nodes_lon, nodes_lat = [], []
            for node in self.G.nodes:
                lat, lon = self.G.nodes[node]['y'], self.G.nodes[node]['x']
                nodes_lat.append(lat)
                nodes_lon.append(lon)
            ax.plot(nodes_lon, nodes_lat, 'b.')
        
        traj = [e[:2] for e in traj]
        wgs_trajs = [gcj2wgs(lat, lon) for lat, lon in traj]
        traj_lat, traj_lon = zip(*wgs_trajs)
        # ax.plot(traj_lon, traj_lat, 'r')
        ax.plot(traj_lon, traj_lat, 'r.')
        matched_points = [(self.G.nodes[i]['y'], self.G.nodes[i]['x']) for i in matched_path]
        matched_points_lat, matched_points_lon = zip(*matched_points)
        ax.plot(matched_points_lon, matched_points_lat, 'g.')
        ax.plot(matched_points_lon, matched_points_lat, 'g')
        
        # plt.xlim([min(traj_lon)-0.001, max(traj_lon)+0.001])
        # plt.ylim([min(traj_lat)-0.001, max(traj_lat)+0.001])

        if time_tag:
            pic_name = self.name + f'-{datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")}'
        else:
            pic_name = self.name
            
        fig.savefig('images/{}.png'.format(pic_name))
