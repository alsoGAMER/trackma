# This file is part of Trackma.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import re
import anitopy
from decimal import Decimal


class AnitopyWrapper():
    """
    Wrapper class around Anitopy, the anime filename parser.
    Exists mainly for compatibility reasons, but also to work around
    some edge cases that Anitopy cannot solve.
    """

    def __init__(self, filename):
        self.file_name = filename
        self.__preProcessFilename()
        self.__parseFilename()

        self.__fixEpisodeNumber()
        self.__fixAnimeTitle()

    def getName(self):
        # Returns the anime title
        return getattr(self, 'anime_title', None)

    def getEpisode(self):
        # Returns the first/only episode number
        if not hasattr(self, 'episode_number'):
            return 1

        if type(self.episode_number) is list:
            return int(self.episode_number[-1])
        return int(self.episode_number)

    def getEpisodeNumbers(self, force_numbers=False):
        # Returns the episode range as a tuple
        (ep_start, ep_end) = (None, None)

        if hasattr(self, 'episode_number'):
            if type(self.episode_number) is list:
                ep_start = Decimal(self.episode_number[0])
                ep_end = Decimal(self.episode_number[-1])
            else:
                ep_start = Decimal(self.episode_number)
                if force_numbers:
                    ep_end = ep_start
        else:
            if force_numbers:
                return (1, 1)

        if force_numbers:
            (ep_start, ep_end) = (int(ep_start), int(ep_end))
        return (ep_start, ep_end)

    def __preProcessFilename(self):
        # Make some adjustments to the filename to increase parsing accuracy

        # Anitopy can parse S01E01 properly, but not S01OVA01, S01S01, S01NCOP01 etc.
        # So we'll need to break things down for the parser.
        m = re.search(
            r'S(?P<season>[0-9]+)(?P<type>[A-Za-z]+)(?P<episode>[0-9]+)',
            self.file_name)
        if m:
            groups = m.groupdict()
            # 'S01E01' -> 'Season 01 - 01'
            if groups['type'] == 'E':
                groups['type'] = ''
            # 'S01S01' -> 'Season 01 Specials - 01'
            if groups['type'] == 'S':
                groups['type'] = 'Specials'
            # for all other cases:
            # 'S01{type}01' -> 'Season 01 {type} - 01'
            self.file_name = (
                self.file_name[:m.start()] + 'Season ' + groups['season']
                + ' ' + groups['type'] + ' - ' + groups['episode']
                + self.file_name[m.end():])

    def __parseFilename(self):
        try:
            for name, value in anitopy.parse(self.file_name).items():
                setattr(self, name, value)
        except Exception:
            # If Anitopy crashes while parsing a filename, print the traceback
            # instead of crashing Trackma altogether.
            import traceback
            traceback.print_exc()

    def __fixAnimeTitle(self):
        # Deal with anime title related stuff that Anitopy left out
        if not hasattr(self, 'anime_title'):
            return

        # Append anime season to the title (if needed)
        if hasattr(self, 'anime_season'):
            if type(self.anime_season) is list:
                season = int(self.anime_season[0])
            else:
                season = int(self.anime_season)
            if season > 1:
                self.anime_title += ' Season ' + str(season)
        # Solve 'Season X Part Y' cases
        if hasattr(self, 'episode_title'):
            m = re.search(r'^Part [2-9]\b', self.episode_title, flags=re.IGNORECASE)
            if m:
                self.anime_title += ' ' + m.group(0)

        # Append anime type to the title (if needed)
        anitype_invalid = ('OP', 'NCOP', 'OPENING', 'ED', 'NCED', 'ENDING', 'PV', 'PREVIEW')
        anitype_specials = ('OAD', 'OAV', 'ONA', 'OVA', 'SPECIAL', 'SPECIALS')
        if hasattr(self, 'anime_type'):
            if type(self.anime_type) is list:
                anitype = self.anime_type
            else:
                anitype = [self.anime_type]
            for t in anitype:
                # Ignore non-episodes such as openings, endings, previews etc.
                if t.upper() in anitype_invalid:
                    for attr in list(self.__dict__.keys()):
                        if attr not in ('file_name', 'anime_type'):
                            delattr(self, attr)
                    return
                if t not in self.anime_title and t.upper() in anitype_specials:
                    self.anime_title += ' ' + t
        else:
            # Fix anime type being detected as episode title
            if hasattr(self, 'episode_title'):
                for t in anitype_specials:
                    m = re.search(
                        r'{0}\b'.format(t),
                        self.episode_title, flags=re.IGNORECASE)
                    if m:
                        self.anime_title += ' ' + m.group(0)

        # Append anime year to the title (if needed)
        if hasattr(self, 'anime_year') and self.anime_year not in self.anime_title:
            self.anime_title += ' (' + self.anime_year + ')'

    def __fixEpisodeNumber(self):
        # Deal with episode related stuff that Anitopy left out
        if not hasattr(self, 'episode_number'):
            return

        # Handle cases like: "[Judas] Naruto - S05E01 (186).mkv"
        # Anitopy should detect the consecutive episode number (186) properly.
        # Just set that as the original episode number, and remove the season value.
        if hasattr(self, 'episode_number_alt'):
            self.episode_number = self.episode_number_alt
            del self.episode_number_alt
            if hasattr(self, 'anime_season'):
                del self.anime_season

        # Unfortunately, we can't have episode numbers like 1A, 1B, 1C etc.
        if type(self.episode_number) is str:
            self.episode_number = re.sub(r'ABCabc', r'', self.episode_number)
