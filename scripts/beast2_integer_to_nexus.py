#!/usr/bin/env python3
"""
Convert integer-coded alignments in a BEAST2 XML file (e.g., one written by
BEAUti) into NEXUS format.

For every <data> element that contains <sequence> elements, the script:

  1. Checks that the <data> element's ``dataType`` attribute is ``integer``.
  2. Checks that every <sequence> has the same ``totalcount``, and that it is
     2 (haploid; symbols "01") or 3 (diploid; symbols "012").
  3. Takes each <sequence>'s ``id`` attribute (verbatim) as the taxon label
     and its ``value`` attribute as the character data.
  4. Checks that every state is in 0..totalcount-1 (or ``?``/``-``) and that
     all sequences have the same length.

Values may be written either as one character per site ("0120?1") or
comma-delimited ("0,1,2,0,?,1"), matching how BEAST2's IntegerData parses
them. Whitespace inside values is ignored.

Output
------
If the XML has one such <data> element, the NEXUS is written to stdout, or to
the path given with -o/--output.

If it has several, each is written to its own file named
``<prefix>-<data id>.nex``, where the prefix is -o/--output if given and
otherwise the input file's path without its extension.

Examples
--------
    beast2_integer_to_nexus.py snapp.xml > snapp.nex
    beast2_integer_to_nexus.py snapp.xml -o snapp.nex
"""

import argparse
import os
import re
import sys
import xml.etree.ElementTree

# Characters that force a NEXUS taxon label to be single-quoted.
_NEXUS_NEEDS_QUOTES = re.compile(r"""[\s()\[\]{}/\\,;:=*'"`+<>-]""")


class ConversionError(Exception):
    """Raised when the XML content cannot be converted."""


def parse_states(value, seq_id):
    """Split a BEAST2 integer sequence string into a list of state tokens."""
    cleaned = re.sub(r"\s+", "", value)
    if "," in cleaned:
        tokens = cleaned.split(",")
        if any(t == "" for t in tokens):
            raise ConversionError(
                "Sequence '{0}' has an empty entry in its comma-delimited "
                "value".format(seq_id)
            )
    else:
        tokens = list(cleaned)
    return tokens


def validate_states(tokens, totalcount, seq_id, missing = "?", gap = "-"):
    """Ensure every token is a valid state for the given totalcount."""
    valid = {str(i) for i in range(totalcount)} | {missing, gap}
    for site, tok in enumerate(tokens, start=1):
        if tok not in valid:
            raise ConversionError(
                "Sequence '{0}' has invalid state '{1}' at site {2}; with "
                "totalcount={3}, allowed states are {4}".format(
                    seq_id, tok, site, totalcount,
                    ", ".join(sorted(valid))
                )
            )


def convert_data_element(data_el, index, missing = "?", gap = "-"):
    """
    Validate one <data> element and return a dict with its label, ploidy
    symbols, and ordered list of (taxon, states) tuples.
    """
    data_id = data_el.get("id", "data{0}".format(index))

    data_type = data_el.get("dataType")
    if data_type != "integer":
        raise ConversionError(
            "<data> element '{0}' has dataType={1!r}; expected 'integer'"
            .format(data_id, data_type)
        )

    seq_els = data_el.findall("sequence")
    if not seq_els:
        raise ConversionError(
            "<data> element '{0}' has no <sequence> elements".format(data_id)
        )

    # Check totalcount before parsing any sequence data.
    totalcounts = {}
    for i, seq_el in enumerate(seq_els, start=1):
        seq_id = seq_el.get("taxon")
        if not seq_id:
            raise ConversionError(
                "Sequence {0} in <data> '{1}' has no taxon attribute".format(
                    i, data_id)
            )
        tc = seq_el.get("totalcount")
        if tc is None:
            raise ConversionError(
                "Sequence '{0}' in <data> '{1}' has no totalcount "
                "attribute".format(seq_id, data_id)
            )
        totalcounts.setdefault(tc.strip(), []).append(seq_id)

    if len(totalcounts) > 1:
        summary = "; ".join(
            "totalcount={0}: {1}".format(tc, ", ".join(ids))
            for tc, ids in sorted(totalcounts.items())
        )
        raise ConversionError(
            "Sequences in <data> '{0}' do not share the same totalcount "
            "({1})".format(data_id, summary)
        )

    tc_str = next(iter(totalcounts))
    if tc_str not in ("2", "3"):
        raise ConversionError(
            "<data> '{0}' has totalcount={1}; only 2 (haploid) or 3 "
            "(diploid) are supported".format(data_id, tc_str)
        )
    totalcount = int(tc_str)

    # Parse and validate sequences.
    taxa = []
    seen = set()
    nchar = None
    for seq_el in seq_els:
        seq_id = seq_el.get("taxon")
        if seq_id in seen:
            raise ConversionError(
                "Duplicate sequence id '{0}' in <data> '{1}'".format(
                    seq_id, data_id)
            )
        seen.add(seq_id)

        value = seq_el.get("value")
        if value is None:
            raise ConversionError(
                "Sequence '{0}' in <data> '{1}' has no value "
                "attribute".format(seq_id, data_id)
            )

        tokens = parse_states(value, seq_id)
        validate_states(tokens, totalcount, seq_id, missing, gap)

        if nchar is None:
            nchar = len(tokens)
        elif len(tokens) != nchar:
            raise ConversionError(
                "Sequence '{0}' in <data> '{1}' has {2} sites, but earlier "
                "sequences have {3}".format(
                    seq_id, data_id, len(tokens), nchar)
            )
        taxa.append((seq_id, tokens))

    if nchar == 0:
        raise ConversionError(
            "Sequences in <data> '{0}' are empty".format(data_id)
        )

    return {
        "id": data_id,
        "symbols": "".join(str(i) for i in range(totalcount)),
        "nchar": nchar,
        "taxa": taxa,
    }


def nexus_label(name):
    """Quote a taxon label for NEXUS if it contains special characters."""
    if _NEXUS_NEEDS_QUOTES.search(name):
        return "'" + name.replace("'", "''") + "'"
    return name


def to_nexus(converted, missing = "?", gap = "-"):
    """Render a converted <data> element as a NEXUS string."""
    labels = [nexus_label(name) for name, _ in converted["taxa"]]
    width = max(len(lab) for lab in labels)
    lines = [
        "#NEXUS",
        "",
        "Begin data;",
        "    Dimensions ntax={0} nchar={1};".format(
            len(converted["taxa"]), converted["nchar"]),
        '    Format datatype=standard symbols="{0}" missing={1} gap={2};'
        .format(converted["symbols"], missing, gap),
        "    Matrix",
    ]
    for label, (_, tokens) in zip(labels, converted["taxa"]):
        lines.append("{0}  {1}".format(label.ljust(width), "".join(tokens)))
    lines.extend(["    ;", "End;", ""])
    return "\n".join(lines)


def safe_filename_part(s):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s)


def main(argv = None):
    parser = argparse.ArgumentParser(
        description = "Convert integer data in a BEAST2 XML file to NEXUS."
    )
    parser.add_argument("xml_path", help = "Path to the BEAST2 XML file.")
    parser.add_argument(
        "-o", "--output",
        help = (
            "Output NEXUS path (one <data> element), or output prefix "
            "(several <data> elements). Default: stdout for one <data> "
            "element; the input path without its extension for several."
        ),
    )
    parser.add_argument(
        '-m', '--missing',
        type = str,
        default = '?',
        help = ('Character for missing data. Default: ?'),
    )
    parser.add_argument(
        '-g', '--gap',
        type = str,
        default = '-',
        help = ('Character for gap. Default: -'),
    )
    args = parser.parse_args(argv)

    try:
        xml_tree = xml.etree.ElementTree.parse(args.xml_path)
    except (xml.etree.ElementTree.ParseError, OSError) as e:
        parser.exit(1, "ERROR: could not read XML '{0}': {1}\n".format(
            args.xml_path, e))

    # Only <data> elements that actually hold sequences; this skips
    # references such as <data idref="..."/>.
    data_els = [d for d in xml_tree.getroot().iter("data")
                if d.find("sequence") is not None]
    if not data_els:
        parser.exit(1, "ERROR: no <data> element with <sequence> children "
                       "found in '{0}'\n".format(args.xml_path))

    try:
        converted = [convert_data_element(d, i, args.missing, args.gap)
                     for i, d in enumerate(data_els, start=1)]
    except ConversionError as e:
        parser.exit(1, "ERROR: {0}\n".format(e))

    if len(converted) == 1:
        nexus = to_nexus(converted[0], args.missing, args.gap)
        if args.output:
            with open(args.output, "w") as out:
                out.write(nexus)
        else:
            sys.stdout.write(nexus)
        return

    prefix = args.output or os.path.splitext(args.xml_path)[0]
    for c in converted:
        path = "{0}-{1}.nex".format(prefix, safe_filename_part(c["id"]))
        with open(path, "w") as out:
            out.write(to_nexus(c, args.missing, args.gap))
        sys.stderr.write("Wrote {0}\n".format(path))


if __name__ == "__main__":
    main()
