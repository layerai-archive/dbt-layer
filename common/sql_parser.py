from typing import List, Optional

import sqlparse  # type:ignore


class LayerSQL(object):
    """
    A parsed Layer SQL statement
    """

    def __init__(self, function_type: str, source_name: str, target_name: str) -> None:
        self.function_type = function_type
        self.source_name = source_name
        self.target_name = target_name

    def __repr__(self) -> str:
        return (
            f"<LayerSQL function_type:{self.function_type}"
            + f" source_name:{self.source_name}"
            + f" target_name:{self.target_name}>"
        )


class LayerSQLParser:
    @classmethod
    def parse(cls, sql: str) -> Optional[LayerSQL]:
        """
        returns None if not a layer SQL statement
        returns an instance of LayerSQL if a valid layer SQL statement
        """
        parsed = sqlparse.parse(sql)
        if len(parsed) == 0:
            return None

        # first strip out whitespace and punctuation from top level
        tokens1 = cls._clean_sql_tokens(parsed[0].tokens)

        # check the top level statement
        if not (
            len(tokens1) == 3
            and tokens1[0].ttype == sqlparse.tokens.DDL
            and tokens1[0].value == "create or replace"
            and tokens1[1].ttype == sqlparse.tokens.Keyword
            and tokens1[1].value == "table"
            and isinstance(tokens1[2], sqlparse.sql.Identifier)
            and tokens1[2].is_group
        ):
            return None

        # then check the next level
        tokens2 = cls._clean_sql_tokens(tokens1[2].tokens)

        if not (len(tokens2) >= 2 and isinstance(tokens2[-1], sqlparse.sql.Identifier)):
            return None

        # get the target name
        target_name = "".join(t.value for t in tokens2[:-1])

        # then check the next level
        tokens3 = cls._clean_sql_tokens(tokens2[-1].tokens)
        if not (len(tokens3) >= 2 and isinstance(tokens3[-1], sqlparse.sql.Parenthesis)):
            return None

        # then check the next level
        tokens4 = cls._clean_sql_tokens(tokens3[-1].tokens)
        if not (
            len(tokens4) == 4
            and tokens4[0].ttype == sqlparse.tokens.DML
            and tokens4[0].value == "select"
            and isinstance(tokens4[1], sqlparse.sql.Identifier)
            and isinstance(tokens4[3], sqlparse.sql.Identifier)
        ):
            return None

        # then check the layer
        tokens5 = tokens4[1].tokens
        if not (
            len(tokens5) == 3
            and tokens5[0].value == "layer"
            and tokens5[0].ttype == sqlparse.tokens.Name
            and tokens5[1].ttype == sqlparse.tokens.Punctuation
            and isinstance(tokens5[2], sqlparse.sql.Function)
        ):
            return None

        function = tokens5[2].tokens
        # get the source name
        source_name = ""
        for token in tokens4[3].tokens:
            if token.is_whitespace:
                break
            source_name += token.value

        return LayerSQL(function[0].value, source_name, target_name)

    @classmethod
    def _clean_sql_tokens(cls, tokens: List[sqlparse.sql.Token]) -> List[sqlparse.sql.Token]:
        """
        Removes whitespace and semicolon punctuation tokens
        """
        return [
            token
            for ix, token in enumerate(tokens)
            if not (
                token.is_whitespace
                or token.value == ";"
                or token.value == "("
                and ix == 0
                or token.value == ")"
                and ix == len(tokens) - 1
            )
        ]
