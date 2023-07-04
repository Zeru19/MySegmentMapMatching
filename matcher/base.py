import os
import datetime
import abc

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

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
        self.G = graph
        self.bgimg = bgimg
        self.extent = extent
        self.matcher = None

    def __call__(self, *args, **kwds):
        return self.match_traj(*args, **kwds)

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
