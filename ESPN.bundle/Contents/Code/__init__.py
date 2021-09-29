import os
import re

base_uri = 'https://site.api.espn.com/apis/site/v2/sports/'

api_map = {
    'Football': [
        {
            'display_name': 'NCAA Football',
            'short_name': 'NCAAF',
            'endpoint': 'college-football',
            'year': 1869,
            'poster': ''
        },
        {
            'display_name': 'National Football League',
            'short_name': 'NFL',
            'endpoint': 'nfl',
            'year': 1920,
            'poster': ''
        },
    ],
    'Baseball': [
        {
            'display_name': "NCAA Men's Baseball",
            'short_name': 'CBASE',
            'endpoint': 'college-baseball',
            'year': 1859,
            'poster': ''
        },
        {
            'display_name': 'Major League Baseball',
            'short_name': 'MLB',
            'endpoint': 'mlb',
            'year': 1903,
            'poster': ''
        },
    ],
    'Basketball': [
        {
            'display_name': "NCAA Men's Basketball",
            'short_name': 'NCAAM',
            'endpoint': 'mens-college-basketball',
            'year': 1891,
            'poster': ''
        },
        {
            'display_name': "NCAA Women's Basketball",
            'short_name': 'NCAAW',
            'endpoint': 'womens-college-basketball',
            'year': 1891,
            'poster': ''
        },
        {
            'display_name': 'National Basketball Association',
            'short_name': 'NBA',
            'endpoint': 'nba',
            'year': 1946,
            'poster': ''
        },
        {
            'display_name': "Women's National Basketball Association",
            'short_name': 'WNBA',
            'endpoint': 'wnba',
            'year': 1997,
            'poster': ''
        },
    ],
    'Hockey': [
        {
            'display_name': 'National Hockey League',
            'short_name': 'NHL',
            'endpoint': 'nhl',
            'year': 1917,
            'poster': ''
        },
    ],
    'Soccer': [
        {
            'display_name': 'Major League Soccer',
            'short_name': 'MLS',
            'endpoint': 'usa.1',
            'year': 1988,
            'poster': ''
        },
        {
            'display_name': 'English Premier League',
            'short_name': 'EPL',
            'endpoint': 'eng.1',
            'year': 1992,
            'poster': ''
        },
    ]
}


def ValidatePrefs():
    pass
    #MessageContainer ('Test', 'This message is a test')


def Start():
    #msgContainer = ValidatePrefs();
    #if msgContainer.header == 'Error': return
    Log.Debug('### ESPN Metadata Agent Started ##############################################################################################################')
    HTTP.CacheTime = CACHE_1HOUR * 24

    HTTP.CacheTime = 0  # only for testing


class ESPNMetadataAgent(Agent.TV_Shows):
    """Agent declaration"""
    name = 'ESPN'
    primary_provider = True
    fallback_agent = False
    contributes_to = None
    languages = [Locale.Language.English]
    accepts_from = ['com.plexapp.agents.localmedia']

    def search(self, results, media, lang, manual):
        """Try to match media either when added or during fix match"""
        Log.Debug("=== Search - Begin - ==============================================================================")

        try:
            show_name = media.show
            Log.Info(show_name)
        except AttributeError:
            pass

        if not show_name:
            return

        for sport in api_map:
            for league in api_map[sport]:

                # compare the title to the search string
                a, b = show_name, league['display_name']
                result_score = 100 - 100 * Util.LevenshteinDistance(a, b) / max(len(a), len(b)) if a != b else 100

                results.Append(
                    MetadataSearchResult(
                        id='{0}/{1}'.format(sport, league['endpoint']),
                        name=league['display_name'],
                        year=league['year'],
                        lang='en',
                        score=result_score
                    )
                )

        # sort the results by score
        results.Sort('score', descending=True)

    def update(self, metadata, media, lang, force):
        Log.Debug("=== Update - Begin - ==============================================================================")
        Log.Info("Update for: {0}".format(metadata.id))

        rating_key = media.id
        Log.Info("Rating key: {0}".format(rating_key))

        # Fill in any missing information for show and download posters/banners
        sport = metadata.id.split('/', 1)[0]
        endpoint = metadata.id.split('/', 1)[-1]

        for league in api_map[sport]:
            if league['endpoint'] == endpoint:
                metadata.title = league['display_name']

                try:
                    metadata.originally_available_at = league['year']
                except:
                    pass

                break

        genres = ['Sports', sport]
        for genre in genres:
            if genre not in metadata.genres:
                metadata.genres.add(genre)

        # no summary available
        #metadata.summary =

        # Work out what episodes we have and match them to ones in the right season
        @parallelize
        def UpdateEpisodes():
            # Go through available seasons
            for season_index in media.seasons:
                season_item = metadata.seasons[season_index]

                # Go through available episodes
                for episode_index in media.seasons[season_index].episodes:
                    episode_item = metadata.seasons[season_index].episodes[episode_index]
                    episode_media = media.seasons[season_index].episodes[episode_index]

                    @task
                    def UpdateEpisode(episode_metadata=episode_item, episode_media_item=episode_media,
                                      show_metadata=metadata):
                        Log.Info("Matching episode number {0}: {1}".format(episode_index, episode_media_item.title))

                        #split_title = episode_media_item.title.split(' ')
                        #Log.Debug(split_title)

                        filename = os.path.splitext(os.path.basename(episode_media.items[0].parts[0].file))[0]
                        Log.Debug(filename)

                        episode_title = filename.rsplit('-', 1)[-1].strip()
                        episode_media_item.title = episode_title
                        Log.Debug(episode_title)

                        split_title = episode_title.split(' ')
                        Log.Debug(split_title)

                        at_types = ['at', 'at.', 'vs', 'vs.']
                        for at_type in at_types:
                            if at_type in split_title:
                                teams = episode_media_item.title.split(" {0} ".format(at_type), 1)
                                if 'at' in at_type:
                                    home_team = teams[-1].strip()
                                    away_team = teams[0].strip()
                                elif 'vs' in at_type:
                                    home_team = teams[0].strip()
                                    away_team = teams[-1].strip()

                                break

                        Log.Info("{0} - Home Team: {1}".format(episode_media_item.title, home_team))
                        Log.Info("{0} - Away Team: {1}".format(episode_media_item.title, away_team))

                        date = episode_media_item.originally_available_at.replace('-', '')
                        Log.Debug("{0} - Date: {1}".format(episode_media_item.title, date))

                        url = "{0}{1}/{2}/scoreboard?dates={3}".format(base_uri, sport.lower(), endpoint, date)

                        search_result = JSON.ObjectFromURL(url, values=None, headers={}, cacheTime=1, encoding=None,
                                                           errors=None, timeout=60, sleep=0)
                        Log.Debug(search_result)

                        for event in search_result['events']:
                            #Log.Info(event)

                            #Log.Debug(event['name'])

                            event_id = None

                            if event['name'] == "{0} at {1}".format(away_team, home_team):
                                event_id = event['id']
                            else:
                                matched = False
                                for competition in event['competitions']:
                                    #Log.Debug(competition)
                                    for competitor in competition['competitors']:
                                        #Log.Debug(competitor)
                                        home_away = competitor['homeAway']
                                        if home_away == 'home':
                                            if competitor['team']['location'].lower() == home_team.lower():
                                                matched = True
                                            else:
                                                matched = False
                                        elif home_away == 'away':
                                            if competitor['team']['location'].lower() == away_team.lower():
                                                matched = True
                                            else:
                                                matched = False
                                    if matched:
                                        event_id = competition['id']
                                        Log.Info("{0} - Event matched: {1}".format(episode_media_item.title, event))
                                        Log.Info("{0} - Event id: {1}".format(episode_media_item.title, event_id))
                                        break

                            if event_id is not None:
                                episode_metadata.title = event['name']
                                event_url = "{0}{1}/{2}/summary?event={3}".format(
                                    base_uri, sport.lower(), endpoint, event_id)

                                event_data = JSON.ObjectFromURL(event_url, values=None, headers={}, cacheTime=1,
                                                encoding=None, errors=None, timeout=60, sleep=0)

                                try:
                                    stadium = event_data['gameInfo']['venue']['fullName']
                                    summary = "{0}\nLive from {1}".format(event['name'], stadium)
                                except KeyError:
                                    pass

                                try:
                                    city = event_data['gameInfo']['venue']['address']['city']
                                    summary = "{0}\nLive from {1} in {2}".format(event['name'], stadium, city)
                                except KeyError:
                                    pass
                                except NameError:
                                    pass

                                try:
                                    state = event_data['gameInfo']['venue']['address']['state']
                                    summary = "{0}\nLive from {1} in {2}, {3}".format(event['name'], stadium, city, state)
                                except KeyError:
                                    pass
                                except NameError:
                                    pass

                                episode_metadata.summary = summary

                                thumbs = []
                                for image in event_data['gameInfo']['venue']['images']:
                                    thumb = image['href']
                                    if thumb not in thumbs:
                                        thumbs.insert(0, thumb)  # insert at index0 reverses order of images

                                y = 0
                                for thumb in thumbs:
                                    if thumb not in episode_metadata.thumbs:
                                        try:
                                            episode_metadata.thumbs[thumb] = Proxy.Media(
                                                HTTP.Request(thumb), sort_order=y)
                                        except:
                                            Log("Failed to add thumbnail for {0}".format(episode_metadata.title))
                                    y += 1

                                episode_metadata.thumbs.validate_keys(thumbs)

                                #episode_metadata.originally_available_at = datetime.datetime.strptime(
                                #    matched_episode['dateEvent'], "%Y-%m-%d").date()
