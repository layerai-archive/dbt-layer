from typing import List, Optional

import sqlparse  # type:ignore
from sqlparse.utils import remove_quotes  # type:ignore


class LayerSqlFunction:
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
        self,
        function_type: str,
        source_name: str,
        target_name: str,
        model_name: str,
        select_columns: List[str],
        predict_columns: List[str],
        sql: str,
    ) -> None:
        super().__init__(function_type=function_type, source_name=source_name, target_name=target_name)
        self.model_name = model_name
        self.select_columns = select_columns
        self.predict_columns = predict_columns
        self.sql = sql


class LayerBuildFunction(LayerSqlFunction):
    pass


class LayerTrainFunction(LayerSqlFunction):
    def __init__(
        self,
        function_type: str,
        source_name: str,
        target_name: str,
        train_columns: List[str],
    ) -> None:
        super().__init__(function_type=function_type, source_name=source_name, target_name=target_name)
        self.train_columns = train_columns


class LayerSQLParser:
    def parse(self, sql: str) -> Optional[LayerSqlFunction]:
        """
        returns None if not a layer SQL statement
        returns an instance of LayerSQL if a valid layer SQL statement
        """
        parsed = sqlparse.parse(sql)
        if len(parsed) == 0:
            return None

        # first strip out whitespace and punctuation from top level
        tokens1 = self._clean_sql_tokens(parsed[0].tokens)

        # check the top level statement
        if not (
            len(tokens1) == 3
            and self.is_keyword(tokens1[0], "create or replace")
            and self.is_keyword(tokens1[1], "table")
            and isinstance(tokens1[2], sqlparse.sql.Identifier)
            and tokens1[2].is_group
        ):
            return None

        # then check the next level
        tokens2 = self._clean_sql_tokens(tokens1[2].tokens)

        if not (len(tokens2) >= 2 and isinstance(tokens2[-1], sqlparse.sql.Identifier)):
            return None

        # get the target name
        target_name = "".join(t.value for t in tokens2[:-1])

        # then check the next level
        tokens3 = self._clean_sql_tokens(tokens2[-1].tokens)
        if not (len(tokens3) >= 2 and isinstance(tokens3[-1], sqlparse.sql.Parenthesis)):
            return None

        # then check the next level
        select_tokens = self._clean_sql_tokens(tokens3[-1].tokens)
        if not (
            self.is_keyword(select_tokens[0], "select")
            and (self.is_identifierlist(select_tokens[1]) or self.is_identifier(select_tokens[1]))
            and self.is_identifier(select_tokens[3])
        ):
            return None

        select_column_tokens = self._clean_sql_tokens(select_tokens[1].tokens)
        function = self.get_layer_function(select_column_tokens)
        # get the source name
        source_name = ""
        for token in select_tokens[3].tokens:
            if token.is_whitespace:
                break
            source_name += token.value

        if self.is_predict_function(function):
            return self._parse_predict(select_tokens, select_column_tokens, function, source_name, target_name)

        if self.is_train_function(function):
            return self._parse_train(function, source_name, target_name)

        return LayerSqlFunction(function[0].value, source_name, target_name)

    def _clean_sql_tokens(self, tokens: List[sqlparse.sql.Token]) -> List[sqlparse.sql.Token]:
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

    def _parse_predict(
        self,
        select_tokens: List[sqlparse.sql.Token],
        select_column_tokens: List[sqlparse.sql.Token],
        func: sqlparse.sql.Function,
        source_name: str,
        target_name: str,
    ) -> Optional[LayerPredictFunction]:
        tokens = self._clean_sql_tokens(func[1].tokens)
        model_name = remove_quotes(tokens[0].value)
        brackets = self._clean_sql_tokens(tokens[3].tokens)
        if self.is_identifierlist(brackets[1]):
            predict_columns = [id.value for id in brackets[1].get_identifiers()]
            select_columns = [
                col.get_name()
                for col in select_column_tokens
                if self.is_identifier(col) and not col.value.startswith("layer.")
            ]
            after_from = self._after_from(select_tokens)
            sql = self._build_cleaned_sql_query(
                list(dict.fromkeys((select_columns + predict_columns))), source_name, after_from
            )
            return LayerPredictFunction(
                func[0].value,
                source_name=source_name,
                target_name=target_name,
                model_name=model_name,
                select_columns=select_columns,
                predict_columns=predict_columns,
                sql=sql,
            )
        return None

    def _parse_train(
        self,
        func: sqlparse.sql.Function,
        source_name: str,
        target_name: str,
    ) -> Optional[LayerTrainFunction]:
        tokens = self._clean_sql_tokens(func[1].tokens)
        if not tokens or str(tokens[0]) == "*":
            train_columns = ["*"]
        else:
            brackets = self._clean_sql_tokens(tokens[1].tokens)
            train_columns = [id.value for id in brackets[1].get_identifiers()]
        return LayerTrainFunction(
            func[0].value,
            source_name=source_name,
            target_name=target_name,
            train_columns=train_columns,
        )

    def is_predict_function(self, func: sqlparse.sql.Function) -> bool:
        return func[0].value.lower() == "predict"

    def is_train_function(self, func: sqlparse.sql.Function) -> bool:
        return func[0].value.lower() == "train"

    def is_keyword(self, token: sqlparse.sql.Token, keyword: str) -> bool:
        return token.is_keyword and token.value.upper() == keyword.upper()

    def is_identifier(self, token: sqlparse.sql.Token) -> bool:
        return isinstance(token, sqlparse.sql.Identifier)

    def is_identifierlist(self, token: sqlparse.sql.Token) -> bool:
        return isinstance(token, sqlparse.sql.IdentifierList)

    def is_function(self, token: sqlparse.sql.Token) -> bool:
        return isinstance(token, sqlparse.sql.Function)

    def get_layer_function(
        self, tokens: List[sqlparse.sql.Token], seen_layer_prefix: bool = False
    ) -> sqlparse.sql.Token:
        layer_function = None
        for token in tokens:
            if token.ttype == sqlparse.tokens.Punctuation:
                continue
            if token.ttype == sqlparse.tokens.Name and token.value == "layer":
                seen_layer_prefix = True
                continue
            if self.is_function(token) and seen_layer_prefix:
                return token
            if self.is_identifier(token):
                layer_function = self.get_layer_function(token.tokens, seen_layer_prefix=seen_layer_prefix)
        return layer_function

    def _build_cleaned_sql_query(self, select_columns: List[str], source_name: str, after_from: str) -> str:
        columns = ", ".join(select_columns)
        quert = f"select {columns} from {source_name} {after_from}"
        return sqlparse.format(quert, keyword_case="lower", strip_whitespace=True)

    def _after_from(self, tokens: List[sqlparse.sql.Token]) -> str:
        from_index = 0
        for idx, token in enumerate(tokens):
            if self.is_keyword(token, "FROM"):
                from_index = idx
        after_from = from_index + 2
        return " ".join(t.value for t in tokens[after_from:])
