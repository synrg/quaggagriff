"""Natural language argument parser module."""
import re
import shlex

from redbot.core.commands import BadArgument

from ...base_classes import PAT_OBS_LINK
from ...core.parsers.constants import ARGPARSE_ARGS, MACROS, REMAINING_ARGS
from .unixlike import UnixlikeParser


class NaturalParser(UnixlikeParser):
    """Natural language query parser."""

    def parse(self, argument: str):
        """Parse natural language argument list."""
        mat = re.search(PAT_OBS_LINK, argument)
        if mat and mat["url"]:
            return argument
        try:
            arg_normalized = re.sub(
                r"((^| )(id|not)) ?by ", r"\2\3-by ", argument, re.I
            )
            arg_normalized = re.sub(
                r"((^| )in ?prj) ", r"\2in-prj ", arg_normalized, re.I
            )
            arg_normalized = re.sub(
                r"((^| )added ?(on|since|until)) ", r"\2added-\3 ", arg_normalized, re.I
            )
            tokens = shlex.split(arg_normalized, posix=False)
        except ValueError as err:
            raise BadArgument(err.args[0]) from err
        ranks = []
        opts = []
        macro_by = ""
        macro_from = ""
        macro_of = ""
        expanded_tokens = []
        # - macro expansions are allowed anywhere in the taxon argument, but
        #   otherwise only when not immediately after an option token
        #   - e.g. `--of rg birds` will expand the `rg` macro, but `--from home`
        #     will not expand the `home` macro
        suppress_macro = False
        arg_count = 0
        expected_args = ARGPARSE_ARGS
        for _token in tokens:
            tok = _token.lower()
            argument_expected = False

            if tok in expected_args:
                tok = f"--{tok}"
            if re.match(r"--", tok):
                arg_count += 1
                # Every option token expects at least one argument.
                argument_expected = True
                if tok == "--of":
                    # Ignore "--of" after it is explicitly inserted.
                    expected_args = REMAINING_ARGS
                    suppress_macro = False
                else:
                    suppress_macro = True
                # Insert at head of explicit "opt" or "rank" any collected
                # ranks or opt macro expansions. This allows them to be
                # combined in the same query, e.g.
                #   `reverse birds opt observed_on=2021-06-13` ->
                #   `--of birds --opt order=asc observed_on=2021-06-13`
                if tok == "--opt" and opts:
                    expanded_tokens.extend(["--opt", *opts])
                    opts = []
                    continue
                # See "Disable rank expansion" comment below. This can probably
                # be reverted if we make that change permanent.
                if tok == "--rank" and ranks:
                    expanded_tokens.extend(["--rank", *ranks])
                    ranks = []
                    continue
                # Discard any prior macro expansions of these; see note below
                if tok == "--by":
                    macro_by = ""
                if tok == "--from":
                    macro_from = ""
                if tok == "--of":
                    macro_of = ""
            if not suppress_macro:
                # Disable rank expansion here to see if this has any impact:
                # - solves "from united kingdom" being incorrectly read
                #   as "--from united --rank kingdom"
                # - if nobody uses it, we're probably better off without it
                # - use "rank kingdom" instead
                #
                # if tok in RANK_KEYWORDS:
                #    ranks.append(tok)
                #    continue
                if tok in MACROS:
                    macro = MACROS[tok]
                    if macro:
                        # Collect any expansions and continue:
                        _macro_opt_args = macro.get("opt")
                        if _macro_opt_args:
                            opts.extend(_macro_opt_args)
                        _macro_by = macro.get("by")
                        if _macro_by:
                            macro_by = _macro_by
                        _macro_from = macro.get("from")
                        if _macro_from:
                            macro_from = _macro_from
                        _macro_of = macro.get("of")
                        if _macro_of:
                            macro_of = _macro_of
                        continue
            # If it's an ordinary word token appearing before all other args,
            # then it's treated implicitly as first word of the "--of" argument,
            # which is inserted here.
            if arg_count == 0:
                arg_count += 1
                expanded_tokens.append("--of")
                macro_of = ""
                expected_args = REMAINING_ARGS
            # Append the ordinary word token:
            expanded_tokens.append(tok)
            # Macros allowed again after first non-ARGS token is consumed:
            if not argument_expected:
                suppress_macro = False

        # Handle collected arguments that were not already
        # inserted into filtered_args above by appending them:
        if ranks:
            expanded_tokens.extend(["--rank", *ranks])
        if opts:
            expanded_tokens.extend(["--opt", *opts])
        # Note: There can only be one of macro_by, macro_from, or macro_of until we support
        # multiple users / places / taxa, so the last user, place, or taxon given wins,
        # superseding anything given earlier in the query.
        if macro_by:
            expanded_tokens.extend(["--by", macro_by])
        if macro_from:
            expanded_tokens.extend(["--from", macro_from])
        if macro_of:
            expanded_tokens.extend(["--of", macro_of])
        # Treat any unexpanded args before the first option keyword
        # argument as implicit "--of" option arguments:
        if not re.match(r"^--", expanded_tokens[0]):
            expanded_tokens.insert(0, "--of")
        argument_normalized = " ".join(expanded_tokens)
        return super().parse(argument_normalized)
