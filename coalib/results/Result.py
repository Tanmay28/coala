from functools import total_ordering
import uuid

from coalib.misc.Decorators import generate_repr
from coalib.results.RESULT_SEVERITY import RESULT_SEVERITY
from coalib.results.SourceRange import SourceRange


@generate_repr("id",
               "origin",
               "affected_code",
               ("severity", RESULT_SEVERITY.reverse.get),
               "message")
@total_ordering
class Result:
    """
    A result is anything that has an origin and a message.

    Optionally it might affect a file.

    When sorting a list of results with the implemented comparison routines
    you will get an ordering which follows the following conditions,
    while the first condition has the highest priority, which descends to the
    last condition.
    2. Results will be sorted by affected code
    4. Results will be sorted by severity (descending, major first, info last)
    5. Results will be sorted by origin (ascending alphabetically)
    6. Results will be sorted by message (ascending alphabetically)
    7. Results will be sorted by debug message (ascending alphabetically)
    """

    def __init__(self,
                 origin,
                 message,
                 affected_code=(),
                 severity=RESULT_SEVERITY.NORMAL,
                 debug_msg="",
                 diffs=None):
        """
        :param origin:        Class name or class of the creator of this object
        :param message:       Message to show with this result
        :param affected_code: A tuple of 0 to n SourceRange objects pointing to
                              related positions in the source code.
        :param severity:      Severity of this result
        :param debug_msg:     A message which may help the user find out why
                              this result was yielded.
        :param diffs:         A dictionary associating a Diff object with each
                              filename.
        """
        origin = origin or ""
        if not isinstance(origin, str):
            origin = origin.__class__.__name__

        self.origin = origin
        self.message = message
        self.debug_msg = debug_msg
        # Sorting is important for tuple comparison
        self.affected_code = tuple(sorted(affected_code))
        self.severity = severity
        self.diffs = diffs
        # Convert debug message to string: some bears pack lists in there which
        # is very useful when exporting the stuff to JSON and further working
        # with the debug data. However, hash can't handle that.
        self.id = uuid.uuid4().int

    @classmethod
    def for_simple_location(cls,
                            origin,
                            message,
                            file,
                            line=None,
                            column=None,
                            end_line=None,
                            end_column=None,
                            severity=RESULT_SEVERITY.NORMAL,
                            debug_msg="",
                            diffs=None):
        ranges = (SourceRange.from_values(file,
                                          line,
                                          column,
                                          end_line,
                                          end_column), )

        return cls(origin=origin,
                   message=message,
                   affected_code=ranges,
                   severity=severity,
                   debug_msg=debug_msg,
                   diffs=diffs)

    def __eq__(self, other):
        # ID isn't relevant for content equality!
        return (isinstance(other, Result) and
                self.origin == other.origin and
                self.message == other.message and
                self.debug_msg == other.debug_msg and
                self.affected_code == other.affected_code and
                self.severity == other.severity and
                self.diffs == other.diffs)

    def __lt__(self, other):
        if not isinstance(other, Result):
            raise TypeError("Comparison with non-result classes is not "
                            "supported.")

        if self.affected_code != other.affected_code:
            return self.affected_code < other.affected_code

        # Both files are equal
        if self.severity != other.severity:
            return self.severity > other.severity

        # Severities are equal, files are equal
        if self.origin != other.origin:
            return self.origin < other.origin

        if self.message != other.message:
            return self.message < other.message

        return self.debug_msg < other.debug_msg

    def to_string_dict(self):
        """
        Makes a dictionary which has all keys and values as strings and
        contains all the data that the base Result has.

        FIXME: diffs are not serialized ATM.

        :return: Dictionary with keys and values as string.
        """
        retval = {}

        members = ["id",
                   "debug_msg",
                   "file",
                   "line_nr",
                   "message",
                   "origin"]

        for member in members:
            value = getattr(self, member)
            retval[member] = "" if value == None else str(value)

        retval["severity"] = str(RESULT_SEVERITY.reverse.get(self.severity, ""))

        return retval

    def apply(self, file_dict):
        """
        Applies all contained diffs to the given file_dict. This operation will
        be done in-place.

        :param file_dict: A dictionary containing all files with filename as
                          key and all lines a value. Will be modified.
        """
        assert isinstance(file_dict, dict)
        assert isinstance(self.diffs, dict)

        for filename in self.diffs:
            file_dict[filename] = self.diffs[filename].apply(
                file_dict[filename])

    def __add__(self, other):
        """
        Joins those patches to one patch.

        :param other: The other patch.
        """
        assert isinstance(self.diffs, dict)
        assert isinstance(other.diffs, dict)

        for filename in other.diffs:
            if filename in self.diffs:
                self.diffs[filename] += other.diffs[filename]
            else:
                self.diffs[filename] = other.diffs[filename]

        return self
