#!/usr/bin/env pypy
"""
Player info management
"""
import os
import pickle

from argparse import ArgumentParser
from utils.query import QueryManager

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('-s', '--start', action='store', dest='start', metavar='n',  default=0, help='Index to begin search')
    parser.add_argument('-e', '--end', action='store', dest='end',  metavar='n', default=10000, help='Index to end search')
    parser.add_argument('-f', '--filename', action='store', dest='filename', default='player.log', metavar='FILE', help='Filename to read/write results')
    parser.add_argument('-d', '--dir', action='store', dest='directory', default='player_data', metavar='DIR', help='Directory to read/write results')
    parser.add_argument('-g', '--game', action='store', dest='game', default='nfl', metavar='ID', help='Game ID to search for players')
    parser.add_argument('-S', '--sleep', action='store', dest='sleep', default=10, metavar='sec', help='Time to wait between queries')
    parser.add_argument('-l', '--league', action='store', dest='league', metavar='ID', help='League ID needed for queries')
    parser.add_argument('-w', '--week', action='store', dest='week',  metavar='n', help='Statisical week number to query', nargs='*')
    parser.add_argument('-F', '--find', action='store_true', dest='find', default=False,
            help='Use with --game/--start/--end/--filename/--dir/--eligible flag, run player ID search on Yahoo DB, --eligible is optional and will NEGATE eligibility check before adding')
    parser.add_argument('--raw', action='store_true', dest='raw', default=False,
            help='Grab player background data, turns --filename into an input flag')
    parser.add_argument('-E', '--eligible', action='store_true', dest='eligible', default=False,
            help='Use with --filename flag, search for eligible players, turns --filename into an input flag')
    parser.add_argument('--loadplayers', action='store_true', dest='load_players', default=False,
            help='<Deprecated as search will automatically do this> Load player data from files into db, use --directory to locate files')
    parser.add_argument('--loadleague', action='store_true', dest='load_league', default=False,
            help='Use with --league flag, load the league id into the db from yahoo')
    parser.add_argument('--stats', action='store_true', dest='stats', default=False,
            help='Use with --week flag, load stat data into db from yahoo')
    args = parser.parse_args()
    kwargs = {
            'start': int(args.start),
            'end': int(args.end),
            'filename': str(args.filename),
            'directory': str(args.directory),
            'game': str(args.game),
            'league': str(args.league),
            }

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy.settings")
    from analyze.models.player import Player
    from analyze.models.league import League
    from analyze.models.team import Team

    if args.find:
        Player.query_manager.set_sleep(int(args.sleep))
        kwargs['eligible'] = args.eligible
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
    elif args.load_players:
        files = os.listdir(args.directory)
        for player_id in files:
            print player_id
            if Player.objects.filter(player_key=player_id).exists():
                continue
            p = Player()
            p.load_raw(player_id, **kwargs)
            p.load_db()
            p.save()
            print '%s %s' % (p.first_name, p.last_name)
    elif args.load_league:
        League.query_manager.set_sleep(int(args.sleep))
        League.load_league(args.league)
        Team.query_manager.set_sleep(int(args.sleep))
        Team.load_teams(args.league)
    elif args.stats:
        Player.query_manager.set_sleep(int(args.sleep))
        for week in args.week:
            Player.get_stats(args.league, int(week), **kwargs)
