from collections import OrderedDict
import json

from coalib.bears.LocalBear import LocalBear
from coalib.results.Result import Result
from coalib.results.Diff import Diff
from coalib.misc.i18n import _


class JSONFormatBear(LocalBear):
    def run(self, filename, file, json_sort: bool=False, indent: int=4):
        try:
            content = ''.join(file)
            json_content = json.loads(content, object_pairs_hook=OrderedDict)
            new_file = json.dumps(json_content,
                                  indent=indent,
                                  sort_keys=json_sort).splitlines(True)
            # Because of a bug we have to strip whitespaces
            new_file = [line.rstrip(" \n")+"\n" for line in new_file]
            if file != new_file:
                diff = Diff.from_string_arrays(file, new_file)

                yield Result(
                    self,
                    _("This file can be reformatted by sorting keys and "
                      "following indentation."),
                    affected_code=diff.affected_code(filename),
                    diffs={filename: diff})
        except (json.decoder.JSONDecodeError, ValueError) as err:
            yield Result.from_values(
                self,
                _("This file does not contain parsable JSON. '{adv_msg}'")
                .format(adv_msg=str(err)),
                file=filename)
