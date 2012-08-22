#!/usr/bin/env pypy
"""
Player info management
"""
from query import QueryManager
import time
import os
import pickle

class Player:

    query_manager = QueryManager()

    def __init__(self, **kwargs):
        self._raw_info = None

    def load_player(self, p_id, **kwargs):
        """
        Load player data from file
        """
        filename = os.path.join(kwargs.get('directory'), p_id)
        with open(filename, 'r') as fread:
            self._raw_info = pickle.load(fread)

    def eligible_player(self, **kwargs):
        """
        Search for eligible players for your league. For example, defensive
        players aren't used in standard formats.
        """
        eligible_positions = kwargs.get('positions', ('O', 'K'))
        position_type = self._raw_info.get('position_type', 'X')
        return position_type in eligible_positions

    @classmethod
    def find_all(cls, **kwargs):
        """
        Since Yahoo is a bitch, go scrub the db and find which player ids
        actually exist
        """

        start = kwargs.get('start', 0)
        end = kwargs.get('end', 10000)
        filename = kwargs.get('filename', 'player.log')
        game = kwargs.get('game', 'nfl')
        with open(filename, 'w') as output:
            for player_id in range(start, end):
                player_id = '%s.p.%04d' % (game, player_id)
                query_str = "select * from fantasysports.players where player_key='%s'" % player_id
                results = QueryManager.decode_query(cls.query_manager.run_yql_query(query_str)).get('query').get('results')
                if results:
                    results = results.get('player')
                    print '%s: True' % player_id
                    output.write('%s\n' % player_id)
                    cls.store_raw_info(player_id, results, **kwargs)
                else:
                    print '%s: False' % player_id
                output.flush()

    @classmethod
    def store_raw_info(cls, p_id, result, **kwargs):
        """
        Grab player info from yahoo and store it locally so that I don't have to rape
        my damn rate limits any time I want some new information
        """
        filename = os.path.join(kwargs.get('directory'), p_id)
        with open(filename, 'w') as output:
            pickle.dump(result, output)

if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-s', '--start', action='store', dest='start', metavar='n',  default=0, help='Index to begin search')
    parser.add_argument('-e', '--end', action='store', dest='end',  metavar='n', default=10000, help='Index to end search')
    parser.add_argument('-f', '--filename', action='store', dest='filename', default='player.log', metavar='FILE', help='Filename to read/write results')
    parser.add_argument('-d', '--dir', action='store', dest='directory', default='player_data', metavar='DIR', help='Directory to read/write results')
    parser.add_argument('-g', '--game', action='store', dest='game', default='nfl', metavar='ID', help='Game ID to search for players')
    parser.add_argument('-S', '--sleep', action='store', dest='sleep', default=10, metavar='sec', help='Time to wait between queries')
    parser.add_argument('-E', '--eligible', action='store_true', dest='eligible', default=False,
            help='Search for eligible players, must use with --league flag, turns --filename into an input flag')
    parser.add_argument('-l', '--league', action='store', dest='league', metavar='ID', help='League ID needed for queries')
    parser.add_argument('--raw', action='store_true', dest='raw', default=False,
            help='Grab player background data, turns --filename into an input flag')
    args = parser.parse_args()
    kwargs = {
            'start': int(args.start),
            'end': int(args.end),
            'filename': str(args.filename),
            'directory': str(args.directory),
            'game': str(args.game),
            'league': str(args.league),
            }
    if args.raw:
        import re
        id_reg = re.compile('(\d+)$')
        query = QueryManager(sleep=args.sleep)
        with open(args.filename, 'r') as source:
            player_list = []
            for player_id in source:
                player_id = player_id.strip()
                if (int(args.start) <= int(id_reg.search(player_id).group(0)) and
                        int(args.end) >= int(id_reg.search(player_id).group(0))):
                    player_list.append(player_id)
            query_str = "select * from fantasysports.players where player_key in (value)"
            for result in query.batch_query(query_str, player_list):
                player_id = result.get('player_key')
                print player_id
                Player.store_raw_info(player_id, result, **kwargs)
    elif args.eligible:
        p = Player()
        with open(args.filename, 'r') as fread:
            with open('%s.new' % args.filename, 'w') as fwrite:
                for player_id in fread:
                    player_id = player_id.strip()
                    filename = os.path.join(args.directory, player_id)
                    if not os.path.exists(filename):
                        continue
                    p.load_player(player_id, **kwargs)
                    pos = p._raw_info.get('position_type')
                    if p.eligible_player():
                        print '%s: %s: True' % (player_id, pos)
                        fwrite.write('%s\n' % player_id)
                    else:
                        print '%s: %s: False' % (player_id, pos)
                        os.unlink(filename)
    else:
        Player.query_manager.set_sleep(int(args.sleep))
        Player.find_all(**kwargs)
