from typing import List, Optional

import sqlparse  # type:ignore
from sqlparse.sql import Token # type:ignore
from sqlparse.tokens import Keyword, DML, Name, Newline, Punctuation # type:ignore
from sqlparse.utils import remove_quotes  # type:ignore
from collections.abc import Callable
from typing import (
    Optional,
    Tuple,
    Callable,
    Iterable,
    Type,
    Dict,
    Any,
    List,
    Mapping,
    Iterator,
    Union,
    Set,
)


class LayerSqlFunction:
    """
    A parsed Layer SQL statement
    """
    SUPPORTED_FUNCTION_TRAIN = "train"
    SUPPORTED_FUNCTION_PREDICT = "predict"
    SUPPORTED_FUNCTION_TYPES = [SUPPORTED_FUNCTION_TRAIN, SUPPORTED_FUNCTION_PREDICT]

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
        source_name: str,
        target_name: str,
        model_name: str,
        select_columns: List[str],
        predict_columns: List[str],
        sql: str,
    ) -> None:
        super().__init__(function_type=self.SUPPORTED_FUNCTION_PREDICT, source_name=source_name, target_name=target_name)
        self.model_name = model_name
        self.select_columns = select_columns
        self.predict_columns = predict_columns
        self.sql = sql


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

    def parse(self, sql:str) -> Optional[LayerSqlFunction]:
        """
        returns None if not a layer SQL statement
        returns an instance of LayerSQL if a valid layer SQL statement
        """
        parsed = sqlparse.parse(sql)
        if not parsed:

            return None
        tokens = parsed[0].tokens
        layer_func = next((x for x in find_functions(tokens) if is_layer_function(x)), None)
        if not layer_func:

            return None
        target_name_group = next((x for x in expect_tokens(tokens, [keyword("create or replace"), group()])), None)
        if not target_name_group:
            return None
        target_name = self._get_target_name_from_group(target_name_group)

        if self.is_predict_function(layer_func):
            return self.parse_predict(layer_func, target_name)
        elif self.is_train_function(layer_func):
            return self._parse_train(layer_func, "", target_name)
        else:
             raise ValueError(f"Unsupported function: {layer_func.get_name()}")
        return None


    def _get_target_name_from_group(self, token: Token) -> str:
            clean_inner_tokens = remove_tokens(token.flatten(), newline())
            target_name_tokens = slice_between_tokens(clean_inner_tokens, name(), whitespace())
            if target_name_tokens :
                return "".join([x.value for x in target_name_tokens])
            else:
                raise ValueError("Invalid sql syntax")

    def parse_predict(self, layer_func_token: Token, target:str) -> LayerPredictFunction:

        # We need the parent `select` statement that contains the function
        # to get access to the selected columns and the source relation
        select_sttmt = find_parent(layer_func_token, lambda x: isinstance(x, sqlparse.sql.Parenthesis))
        if not select_sttmt:
            return None
        clean_select_sttmt = clean_separators(select_sttmt)

        # sqlparse doesn't seem to parse correctly the inner contents of this parenthesis.
        # Here, we rebuild the sql and use parse it again to get the relevant tokens
        inner_sql_text = " ".join(x.value for x in clean_select_sttmt)
        inner_sql = sqlparse.parse(inner_sql_text)[0]
        clean_inner_sql = remove_tokens(inner_sql.tokens,lambda x:x.is_whitespace)

        # extract the source relation
        from_token = expect_tokens(clean_inner_sql, [keyword("from"), lambda x: isinstance(x, sqlparse.sql.Identifier)])
        if not from_token:
            raise ValueError("Invalid sql")
        source = from_token[0].value
        where_statement = " ".join((x.value for x in from_token[1:]))

        # extract the selected columns in the query
        select_columns_list = find_token(clean_inner_sql, lambda x:isinstance(x, sqlparse.sql.IdentifierList))
        columns_incl_layer = find_tokens(select_columns_list.tokens, lambda x:isinstance(x,sqlparse.sql.Identifier))
        find_layer_token = lambda x: find_layer_function(x) is not None
        layer_column = find_token(columns_incl_layer, find_layer_token)
        columns = remove_tokens(columns_incl_layer, find_layer_token)
        select_columns = [t.value for t in columns]

        predict_column_name = get_predict_function_name(layer_column)

        # extract the layer prediction function
        clean_func_tokens = clean_separators(layer_func_token[1].tokens)
        if len(clean_func_tokens) < 3:
            invalid_func = " ".join(t.value for t in clean_func_tokens)
            raise ValueError(f"Invalid predict function syntax {invalid_func}")
        model_name, array_lit, bracket_container = clean_func_tokens
        predict_model = model_name.value[1:-1] # remove quotes
        predict_cols = self.get_predict_cols(bracket_container)

        all_columns = select_columns + list(set(predict_cols) - set(select_columns))
        sql = self.build_sql(all_columns, source, where_statement)

        return LayerPredictFunction(source, target, predict_model, select_columns, predict_cols, sql)

    def get_predict_cols(self, brace_container_token: Token) -> List[str]:
        open_brace, predict_cols_token, close_brace = brace_container_token.tokens
        if isinstance(predict_cols_token, sqlparse.sql.IdentifierList):
            return [x.value for x in clean_separators(predict_cols_token.tokens)]
        return [predict_cols_token.value]

    def build_sql(self, cols:Set[str], source:str, where_statement: str) -> str:
        col_str = ", ".join(cols)
        if len(where_statement) > 0:
            return f"select {col_str} from {source} {where_statement}"
        else:
            return f"select {col_str} from {source}"


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
        if len(tokens) < 1:
            raise ValueError("Invalid predict function syntax")
        model_name = remove_quotes(tokens[0].value)
        if len(tokens) < 3:
            sql = " ".join(t.value for t in tokens)
            raise ValueError(f"Invalid predict function syntax {sql}")
        brackets = self._clean_sql_tokens(tokens[3].tokens)
        if self.is_identifierlist(brackets[1]):
            predict_columns = [id.value for id in brackets[1].get_identifiers()]
        else:
            predict_columns = [brackets[1].value]
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

## Functions to assist the SQL Parsing

TokenPredicate = Callable[[Token], bool]

def get_predict_function_name(layer_column_token: Token) -> Optional[str]:
    if layer_column_token.has_alias():
        return layer_column_token.get_name()
    return "predict"


def find_token(tokens: List[Token], pred: TokenPredicate) -> Optional[Token] :
    for token in tokens:
        if pred(token):
            return token
    return None


def find_tokens(tokens: List[Token], pred: TokenPredicate) -> List[Token] :
    return [x for x in tokens if pred(x)]


def remove_tokens(tokens:List[Token], pred: TokenPredicate) -> List[Token]:
    return [x for x in tokens if not pred(x)]


def clean_separators(tokens: List[Token]) -> List[Token]:
    return remove_tokens(tokens, lambda x:x.is_whitespace or x.ttype == Punctuation)


def expect_tokens(tokens:List[Token], predicates: List[Callable[[Token], bool]]) -> Optional[List[Token]]:
    if not tokens:
        return None
    if not predicates:
        return tokens
    pred = predicates[0]
    for i, token in enumerate(tokens):
        if pred(token):
            return expect_tokens(tokens[i:],predicates[1:])


def slice_between_tokens(tokens:List[Token], start: Callable[[Token], bool], end:  Callable[[Token], bool]) -> Optional[List[Token]]:
    if not tokens:
        return None
    start_index = None
    end_index = None
    start_seen = False
    for i, token in enumerate(tokens):
        if not start_seen and start(token):
            start_index = i
            start_seen = True
        if start_seen and end(token):
            end_index = i
            break
    if start_index>=0 and end_index>0:
        return tokens[start_index:end_index]
    else:
        return None


def find_functions(elem: Any) -> List[Token]:
    from itertools import chain
    funcs = [[]]
    if isinstance(elem, List):
        funcs = [find_functions(x) for x in elem]
    elif isinstance(elem, sqlparse.sql.Statement):
        funcs = [find_functions(x) for x in elem.tokens]
    elif isinstance(elem, sqlparse.sql.IdentifierList):
        funcs = [find_functions(x) for x in elem.get_identifiers()]
    elif isinstance(elem, sqlparse.sql.Identifier):
        funcs = [find_functions(x) for x in elem.tokens]
    elif isinstance(elem, sqlparse.sql.Parenthesis):
        funcs = [find_functions(x) for x in elem.tokens]
    elif isinstance(elem, sqlparse.sql.Function):
        return [elem]
    return list(chain.from_iterable(funcs))


def find_parent(token:Token, pred: TokenPredicate) -> Optional[Token]:
    parent = token.parent
    if not parent:
        return None
    elif (pred(parent)):
        return parent
    else:
        return find_parent(parent, pred)


def is_layer_function(func: sqlparse.sql.Function) -> bool:
    parent = func.parent
    return isinstance(parent, sqlparse.sql.Identifier) and parent.tokens[0].value == 'layer'


def find_layer_function(tokens: List[Token]) -> Optional[Token]:
    return next((x for x in find_functions(tokens) if is_layer_function(x)), None)

def keyword(value:str) -> Callable[[Token], bool]:
    def checkToken(token: Token)-> bool:
        return token.is_keyword and token.value.lower() == value.lower()
    return checkToken

def whitespace() -> Callable[[Token], bool]:
    return lambda x:x.is_whitespace

def name() -> Callable[[Token], bool]:
    return lambda x:x.ttype is Name

def newline() -> Callable[[Token], bool]:
    return lambda x:x.ttype is Newline

def group() -> Callable[[Token], bool]:
    return lambda x:x.is_group

