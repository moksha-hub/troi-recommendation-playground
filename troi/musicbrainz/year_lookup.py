import re
import sys
import uuid
from urllib.parse import quote

import requests
import ujson

from troi import Element, Artist, Recording, PipelineError

class YearLookupElement(Element):
    '''
        Look up musicbrainz earliest release year for a list of recordings, based on artist credit name and recording name.
    '''

    SERVER_URL = "http://bono.metabrainz.org:8000/acrp-year-lookup/json"

    def __init__(self):
        Element.__init__(self)

    @staticmethod
    def inputs():
        return [ Recording ]

    @staticmethod
    def outputs():
        return [ Recording ]

    def read(self, inputs, debug=False):

        recordings = inputs[0]
        if not recordings:
            return []

        data = []
        for r in recordings:
            data.append({ '[recording_name]': r.name, 
                          '[artist_credit_name]': r.artist.name })

        r = requests.post(self.SERVER_URL, json=data)
        if r.status_code != 200:
            raise PipelineError("Cannot fetch recording years from MusicBrainz: HTTP code %d" % r.status_code)

        try:
            rows = ujson.loads(r.text)
        except ValueError as err:
            raise PipelineError("Cannot fetch recording years from MusicBrainz: " + str(err))

        mbid_index = {}
        for row in rows:
            mbid_index[row['artist_credit_name'] + row['recording_name']] = row['year']

        output = []
        for r in recordings:
            try:
                r.year = mbid_index[r.artist.name + r.name]
            except KeyError:
                self.debug("recording (%s %s) not found, skipping." % (r.artist.name, r.name))
                continue

            output.append(r)

        return output
