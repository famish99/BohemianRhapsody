#!/usr/bin/env pypy
"""
Player info management
"""
from utils.query import QueryManager
from analyze.models.player import Player
import os
import pickle

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
    parser.add_argument('-F', '--find', action='store_true', dest='find', default=False, help='Run player ID search on Yahoo DB')
    args = parser.parse_args()
    kwargs = {
            'start': int(args.start),
            'end': int(args.end),
            'filename': str(args.filename),
            'directory': str(args.directory),
            'game': str(args.game),
            'league': str(args.league),
            }
    if args.find:
        Player.query_manager.set_sleep(int(args.sleep))
        Player.find_all(**kwargs)
    elif args.raw:
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
                    p.load_raw(player_id, **kwargs)
                    pos = p._raw_info.get('position_type')
                    if p.eligible_player():
                        print '%s: %s: True' % (player_id, pos)
                        fwrite.write('%s\n' % player_id)
                    else:
                        print '%s: %s: False' % (player_id, pos)
                        os.unlink(filename)
