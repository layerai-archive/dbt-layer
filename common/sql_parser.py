from typing import List, Optional

import sqlparse  # type:ignore


class LayerSqlFunction(object):
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


class LayerPredictFunction(LayerSqlFunction):
    def __init__(
        self, function_type: str, source_name: str, target_name: str, columns_for_prediction: List[str]
    ) -> None:
        super().__init__(function_type=function_type, source_name=source_name, target_name=target_name)
        self.columns_for_prediction = columns_for_prediction


class LayerBuildFunction(LayerSqlFunction):
    pass


class LayerTrainFunction(LayerSqlFunction):
    pass


class LayerSQLParser:
    @classmethod
    def parse(cls, sql: str) -> Optional[LayerSqlFunction]:
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
            and cls.is_keyword(tokens1[0], "create or replace")
            and cls.is_keyword(tokens1[1], "table")
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
            and cls.is_keyword(tokens4[0], "select")
            and (cls.is_identifierlist(tokens4[1]) or cls.is_identifier(tokens4[1]))
            and cls.is_identifier(tokens4[3])
        ):
            return None

        tokens5 = cls._clean_sql_tokens(tokens4[1].tokens)
        function = cls.get_layer_function(tokens5)
        # get the source name
        source_name = ""
        for token in tokens4[3].tokens:
            if token.is_whitespace:
                break
            source_name += token.value

        return LayerSqlFunction(function[0].value, source_name, target_name)

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

    def is_keyword(token: sqlparse.sql.Token, keyword: str) -> bool:
        return token.is_keyword and token.value.upper() == keyword.upper()

    def is_identifier(token: sqlparse.sql.Token) -> bool:
        return isinstance(token, sqlparse.sql.Identifier)

    def is_identifierlist(token: sqlparse.sql.Token) -> bool:
        return isinstance(token, sqlparse.sql.IdentifierList)

    def is_function(token: sqlparse.sql.Token) -> bool:
        return isinstance(token, sqlparse.sql.Function)

    @classmethod
    def get_layer_function(
        cls, tokens: List[sqlparse.sql.Token], seen_layer_prefix: bool = False
    ) -> sqlparse.sql.Token:
        layer_function = None
        for token in tokens:
            if token.ttype == sqlparse.tokens.Punctuation:
                continue
            if token.ttype == sqlparse.tokens.Name and token.value == "layer":
                seen_layer_prefix = True
                continue
            if cls.is_function(token) and seen_layer_prefix:
                return token
            if cls.is_identifier(token):
                layer_function = cls.get_layer_function(token.tokens, seen_layer_prefix=seen_layer_prefix)
        return layer_function
